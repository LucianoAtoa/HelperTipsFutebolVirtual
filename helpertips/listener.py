#!/usr/bin/env python3
"""HelperTips Listener — captures signals from {VIP} ExtremeTips Telegram group."""

import asyncio
import logging
import os
import signal
import sys

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from telethon import TelegramClient, events

from helpertips.db import ensure_schema, get_connection, validate_config
from helpertips.list_groups import selecionar_grupo
from helpertips.parser import parse_message
from helpertips.store import get_stats, log_parse_failure, upsert_signal

# ---------------------------------------------------------------------------
# Logging configuration — RichHandler em TTY, RotatingFileHandler em daemon
# ---------------------------------------------------------------------------

LOG_PATH = "/var/log/helpertips/listener.log"


def configure_logging():
    """Configura logging: RichHandler em TTY, RotatingFileHandler em daemon."""
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)
    # Limpar handlers existentes para evitar duplicacao
    root_logger.handlers.clear()

    if sys.stdout.isatty():
        from rich.logging import RichHandler
        handler = RichHandler(rich_tracebacks=True, show_path=False)
        handler.setLevel(logging.INFO)
        root_logger.addHandler(handler)
    else:
        from logging.handlers import RotatingFileHandler
        handler = RotatingFileHandler(
            LOG_PATH,
            maxBytes=10 * 1024 * 1024,  # 10MB
            backupCount=7,
            encoding="utf-8",
        )
        handler.setFormatter(logging.Formatter(
            "%(asctime)s %(levelname)s %(name)s: %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        ))
        handler.setLevel(logging.INFO)
        root_logger.addHandler(handler)


configure_logging()
logger = logging.getLogger("helpertips")

# ---------------------------------------------------------------------------
# Rich console instance for formatted output
# ---------------------------------------------------------------------------

console = Console()

# ---------------------------------------------------------------------------
# Section 2: Parse coverage tracking (PARS-07)
# ---------------------------------------------------------------------------

parse_total = 0
parse_success = 0
parse_fail_count = 0

# Module-level connection — set in main(), shared with event handlers via closure
conn = None

# ---------------------------------------------------------------------------
# Section 4: Startup summary (TERM-01, TERM-02) — rich Panel with Table (D-03)
# ---------------------------------------------------------------------------

def print_startup_summary(conn, group_titles):
    """Print a formatted startup summary — rich Panel em TTY, logger.info em daemon.

    Parameters
    ----------
    conn : psycopg2 connection
        Open database connection for stats query.
    group_titles : list[str]
        List of group title strings (e.g. ["{VIP} ExtremeTips (123456)", "Ambas Marcam (789012)"]).
    """
    stats = get_stats(conn)  # returns dict with total, greens, reds, pending, parse_failures, coverage
    taxa = (stats['greens'] / stats['total'] * 100) if stats['total'] > 0 else 0.0

    if sys.stdout.isatty():
        table = Table(title="Estatisticas", show_header=True, header_style="bold cyan")
        table.add_column("Metrica", style="bold")
        table.add_column("Valor", justify="right")

        table.add_row("Total de sinais", str(stats['total']))
        table.add_row("[green]GREEN[/green]", str(stats['greens']))
        table.add_row("[red]RED[/red]", str(stats['reds']))
        table.add_row("Pendentes", str(stats['pending']))
        table.add_row("Taxa de acerto", f"{taxa:.1f}%")
        table.add_row("Cobertura parser", f"{stats['coverage']:.1f}%")
        table.add_row("Falhas de parse", str(stats['parse_failures']))

        panel = Panel(
            table,
            title=f"[bold]HelperTips[/bold] - {', '.join(group_titles)}",
            subtitle="Ctrl+C para encerrar",
            border_style="blue",
        )
        console.print(panel)
    else:
        logger.info(
            "HelperTips iniciado — grupo: %s | total: %d | greens: %d | reds: %d | taxa: %.1f%% | cobertura: %.1f%%",
            ', '.join(group_titles), stats['total'], stats['greens'], stats['reds'], taxa, stats['coverage'],
        )

# ---------------------------------------------------------------------------
# Section 5: Main async function
# ---------------------------------------------------------------------------

async def main():
    global conn, parse_total, parse_success, parse_fail_count

    # Section 1: Configuration — validate_config() fails fast before any connection
    validate_config()

    api_id = int(os.environ['TELEGRAM_API_ID'])
    api_hash = os.environ['TELEGRAM_API_HASH']

    # Parse TELEGRAM_GROUP_IDS (CSV) com fallback para TELEGRAM_GROUP_ID (D-14)
    group_ids_str = os.environ.get('TELEGRAM_GROUP_IDS') or os.environ.get('TELEGRAM_GROUP_ID', '')
    group_ids = [int(g.strip()) for g in group_ids_str.split(',') if g.strip()]

    client = TelegramClient('helpertips_listener', api_id, api_hash)
    await client.start()
    logger.info("Telegram conectado")

    # Se group_ids vazio, oferecer selecao interativa em TTY ou abortar em daemon
    if not group_ids:
        if sys.stdout.isatty():
            console.print("[yellow]TELEGRAM_GROUP_IDS nao configurado.[/yellow]")
            # Oferecer selecao interativa se TTY
            selected = await selecionar_grupo(client)
            if selected is None:
                console.print("[red]Nenhum grupo selecionado. Encerrando.[/red]")
                await client.disconnect()
                sys.exit(1)
            group_ids = [selected]
        else:
            logger.error("TELEGRAM_GROUP_IDS vazio ou invalido. Encerrando.")
            await client.disconnect()
            sys.exit(1)

    # Database connection
    conn = get_connection()
    ensure_schema(conn)
    logger.info("Database connected, schema verified")

    # Verificar acesso a cada grupo (D-03)
    group_titles = []
    invalid_ids = []
    for gid in group_ids:
        try:
            entity = await client.get_entity(gid)
            group_titles.append(f"{entity.title} ({gid})")
        except Exception as e:
            logger.error("Nao foi possivel acessar grupo %s: %s", gid, e)
            invalid_ids.append(gid)

    if invalid_ids:
        logger.warning("Grupos invalidos ignorados: %s", invalid_ids)
        group_ids = [g for g in group_ids if g not in invalid_ids]

    if not group_ids:
        logger.error("Nenhum grupo valido encontrado. Encerrando.")
        conn.close()
        await client.disconnect()
        sys.exit(1)

    # Handler multi-grupo — definido apos group_ids estar finalizado (D-01)
    # Usa add_event_handler para registro dinamico apos filtragem de grupos invalidos
    async def handle_signal(event):
        """Handle incoming and edited signal messages from the VIP Telegram groups."""
        global parse_total, parse_success, parse_fail_count

        # LIST-04: ignore media, stickers, photos — only process text messages
        if not event.message.text:
            return

        parse_total += 1

        parsed = parse_message(event.message.text, event.message.id)

        if parsed is None:
            parse_fail_count += 1
            reason = "no_liga_match"  # parser returns None when no LIGA match found
            logger.warning("Parse falhou: %.80s...", event.message.text.replace('\n', ' '))
            await asyncio.to_thread(log_parse_failure, conn, event.message.text, reason)
            return

        parse_success += 1

        # Adicionar group_id ao dict do parsed signal (D-01)
        parsed['group_id'] = event.chat_id

        # DB-04: CRITICAL — never call upsert_signal() directly from async handler.
        # psycopg2 makes blocking syscalls; asyncio.to_thread() wraps it safely.
        await asyncio.to_thread(upsert_signal, conn, parsed)

        # D-03, D-05: colored output per resultado (GREEN=verde, RED=vermelho, NOVO=amarelo)
        resultado = parsed.get('resultado')
        if sys.stdout.isatty():
            if resultado == 'GREEN':
                console.print(f"  [bold green]GREEN[/bold green] | {parsed['liga']} | {parsed['entrada']}")
            elif resultado == 'RED':
                console.print(f"  [bold red]RED[/bold red] | {parsed['liga']} | {parsed['entrada']}")
            else:
                console.print(f"  [yellow]NOVO[/yellow] | {parsed['liga']} | {parsed['entrada']}")
        else:
            logger.info("%s | %s | %s", resultado or "NOVO", parsed['liga'], parsed['entrada'])

    client.add_event_handler(handle_signal, events.NewMessage(chats=group_ids))
    client.add_event_handler(handle_signal, events.MessageEdited(chats=group_ids))

    # Print startup summary (TERM-01)
    print_startup_summary(conn, group_titles)

    # Graceful shutdown (TERM-03) — SIGINT future so we can await it cleanly
    loop = asyncio.get_running_loop()
    stop = loop.create_future()

    def handle_sigint():
        if not stop.done():
            stop.set_result(None)

    loop.add_signal_handler(signal.SIGINT, handle_sigint)

    try:
        await stop
    finally:
        if parse_total > 0:
            coverage = (parse_success / parse_total * 100)
            if sys.stdout.isatty():
                console.print(f"\n[bold]Sessao encerrada[/bold] — cobertura: {coverage:.1f}% ({parse_success}/{parse_total})")
            else:
                logger.info("Sessao encerrada — cobertura: %.1f%% (%d/%d)", coverage, parse_success, parse_total)
        else:
            if sys.stdout.isatty():
                console.print("\n[bold]Sessao encerrada[/bold] — nenhuma mensagem processada")
            else:
                logger.info("Sessao encerrada — nenhuma mensagem processada")
        conn.close()
        await client.disconnect()

# ---------------------------------------------------------------------------
# Section 6: Entry point with auto-reconnect (LIST-05)
# ---------------------------------------------------------------------------

if __name__ == '__main__':
    MAX_RETRIES = 5
    retry_delay = 5  # seconds, grows exponentially up to 60s

    for attempt in range(1, MAX_RETRIES + 1):
        try:
            asyncio.run(main())
            break  # Clean exit (Ctrl+C handled inside main via SIGINT future)
        except ConnectionError as e:
            logger.warning("Connection lost (attempt %d/%d): %s", attempt, MAX_RETRIES, e)
            if attempt < MAX_RETRIES:
                logger.info("Reconnecting in %ds...", retry_delay)
                import time
                time.sleep(retry_delay)
                retry_delay = min(retry_delay * 2, 60)  # Exponential backoff, max 60s
            else:
                logger.error("Max retries reached. Exiting.")
                sys.exit(1)
        except KeyboardInterrupt:
            if sys.stdout.isatty():
                console.print("\n[bold]Bye![/bold]")
            else:
                logger.info("Listener encerrado via KeyboardInterrupt")
            break

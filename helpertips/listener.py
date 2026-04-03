#!/usr/bin/env python3
"""HelperTips Listener — captures signals from {VIP} ExtremeTips Telegram group."""

import asyncio
import os
import signal
import sys
import logging
from telethon import TelegramClient, events
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.logging import RichHandler
from helpertips.db import validate_config, get_connection, ensure_schema
from helpertips.parser import parse_message
from helpertips.store import upsert_signal, get_stats, log_parse_failure
from helpertips.list_groups import selecionar_grupo

# ---------------------------------------------------------------------------
# Logging configuration — RichHandler integrates with stdlib logging (D-04)
# ---------------------------------------------------------------------------

logging.basicConfig(
    level=logging.INFO,
    format="%(message)s",
    datefmt="[%X]",
    handlers=[RichHandler(rich_tracebacks=True, show_path=False)],
)
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

def print_startup_summary(conn, group_title):
    """Print a formatted startup summary using rich Panel and Table."""
    stats = get_stats(conn)  # returns dict with total, greens, reds, pending, parse_failures, coverage

    table = Table(title="Estatisticas", show_header=True, header_style="bold cyan")
    table.add_column("Metrica", style="bold")
    table.add_column("Valor", justify="right")

    table.add_row("Total de sinais", str(stats['total']))
    table.add_row("[green]GREEN[/green]", str(stats['greens']))
    table.add_row("[red]RED[/red]", str(stats['reds']))
    table.add_row("Pendentes", str(stats['pending']))

    taxa = (stats['greens'] / stats['total'] * 100) if stats['total'] > 0 else 0.0
    table.add_row("Taxa de acerto", f"{taxa:.1f}%")
    table.add_row("Cobertura parser", f"{stats['coverage']:.1f}%")
    table.add_row("Falhas de parse", str(stats['parse_failures']))

    panel = Panel(
        table,
        title=f"[bold]HelperTips[/bold] - {group_title}",
        subtitle="Ctrl+C para encerrar",
        border_style="blue",
    )
    console.print(panel)

# ---------------------------------------------------------------------------
# Section 5: Main async function
# ---------------------------------------------------------------------------

async def main():
    global conn, parse_total, parse_success, parse_fail_count

    # Section 1: Configuration — validate_config() fails fast before any connection
    validate_config()

    api_id = int(os.environ['TELEGRAM_API_ID'])
    api_hash = os.environ['TELEGRAM_API_HASH']
    group_id_str = os.environ.get('TELEGRAM_GROUP_ID', '').strip()

    client = TelegramClient('helpertips_listener', api_id, api_hash)
    await client.start()
    logger.info("Telegram conectado")

    # Se TELEGRAM_GROUP_ID não está configurado, oferece seleção interativa
    if not group_id_str:
        console.print("[yellow]TELEGRAM_GROUP_ID não configurado.[/yellow]")
        group_id = await selecionar_grupo(client)
        if group_id is None:
            console.print("[red]Nenhum grupo selecionado. Encerrando.[/red]")
            await client.disconnect()
            sys.exit(1)
    else:
        group_id = int(group_id_str)

    @client.on(events.NewMessage(chats=group_id))
    @client.on(events.MessageEdited(chats=group_id))
    async def handle_signal(event):
        """Handle incoming and edited signal messages from the VIP Telegram group."""
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

        # DB-04: CRITICAL — never call upsert_signal() directly from async handler.
        # psycopg2 makes blocking syscalls; asyncio.to_thread() wraps it safely.
        await asyncio.to_thread(upsert_signal, conn, parsed)

        # D-03, D-05: colored output per resultado (GREEN=verde, RED=vermelho, NOVO=amarelo)
        resultado = parsed.get('resultado')
        if resultado == 'GREEN':
            console.print(f"  [bold green]GREEN[/bold green] | {parsed['liga']} | {parsed['entrada']}")
        elif resultado == 'RED':
            console.print(f"  [bold red]RED[/bold red] | {parsed['liga']} | {parsed['entrada']}")
        else:
            console.print(f"  [yellow]NOVO[/yellow] | {parsed['liga']} | {parsed['entrada']}")

    # Database connection
    conn = get_connection()
    ensure_schema(conn)
    logger.info("Database connected, schema verified")

    # Verify group access (TERM-02) — confirms group name for startup summary
    try:
        entity = await client.get_entity(group_id)
        group_title = entity.title
    except Exception as e:
        logger.error("Cannot access group %s: %s", group_id, e)
        logger.error("Check TELEGRAM_GROUP_ID in .env")
        conn.close()
        sys.exit(1)

    # Print startup summary (TERM-01)
    print_startup_summary(conn, group_title)

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
            console.print(f"\n[bold]Sessao encerrada[/bold] — cobertura: {coverage:.1f}% ({parse_success}/{parse_total})")
        else:
            console.print("\n[bold]Sessao encerrada[/bold] — nenhuma mensagem processada")
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
            console.print("\n[bold]Bye![/bold]")
            break

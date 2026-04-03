#!/usr/bin/env python3
"""HelperTips Listener — captures signals from {VIP} ExtremeTips Telegram group."""

import asyncio
import os
import signal
import sys
import logging
from telethon import TelegramClient, events
from helpertips.db import validate_config, get_connection, ensure_schema
from helpertips.parser import parse_message
from helpertips.store import upsert_signal, get_stats

# ---------------------------------------------------------------------------
# Logging configuration
# ---------------------------------------------------------------------------

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Section 2: Parse coverage tracking (PARS-07)
# ---------------------------------------------------------------------------

parse_total = 0
parse_success = 0
parse_failures = 0

# Module-level connection — set in main(), shared with event handlers via closure
conn = None

# ---------------------------------------------------------------------------
# Section 4: Startup summary (TERM-01, TERM-02)
# ---------------------------------------------------------------------------

def print_startup_summary(conn, group_title):
    """Print a formatted startup summary with DB stats and group connection info."""
    total, greens, reds, pending = get_stats(conn)
    taxa = (greens / total * 100) if total > 0 else 0.0
    print("=" * 50)
    print("  HelperTips Listener")
    print(f"  Connected to: {group_title}")
    print(f"  Signals in DB: {total}")
    print(f"  GREEN: {greens} | RED: {reds} | Pending: {pending}")
    print(f"  Win rate: {taxa:.1f}%")
    print("=" * 50)
    print("Listening for new signals... (Ctrl+C to stop)")

# ---------------------------------------------------------------------------
# Section 5: Main async function
# ---------------------------------------------------------------------------

async def main():
    global conn, parse_total, parse_success, parse_failures

    # Section 1: Configuration — validate_config() fails fast before any connection
    validate_config()

    api_id = int(os.environ['TELEGRAM_API_ID'])
    api_hash = os.environ['TELEGRAM_API_HASH']
    group_id = int(os.environ['TELEGRAM_GROUP_ID'])

    # Section 3: Event handler — registered inside main() after client is created
    # Uses closure over group_id and conn (module-level)
    client = TelegramClient('helpertips_listener', api_id, api_hash)

    @client.on(events.NewMessage(chats=group_id))
    @client.on(events.MessageEdited(chats=group_id))
    async def handle_signal(event):
        """Handle incoming and edited signal messages from the VIP Telegram group."""
        global parse_total, parse_success, parse_failures

        # LIST-04: ignore media, stickers, photos — only process text messages
        if not event.message.text:
            return

        parse_total += 1

        parsed = parse_message(event.message.text, event.message.id)

        if parsed is None:
            parse_failures += 1
            logger.warning(
                "Parse failure (not a signal): %.50s...",
                event.message.text.replace('\n', ' ')
            )
            return

        parse_success += 1

        # DB-04: CRITICAL — never call upsert_signal() directly from async handler.
        # psycopg2 makes blocking syscalls; asyncio.to_thread() wraps it safely.
        await asyncio.to_thread(upsert_signal, conn, parsed)

        logger.info(
            "Signal saved: %s | %s | resultado=%s",
            parsed['liga'],
            parsed['entrada'],
            parsed['resultado'],
        )

    # Database connection
    conn = get_connection()
    ensure_schema(conn)
    logger.info("Database connected, schema verified")

    # Telethon connection — client.start() handles the interactive auth flow
    # on first run (phone number prompt, verification code, optional 2FA)
    await client.start()
    logger.info("Telegram client started")

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
        print("\nShutting down gracefully...")
        if parse_total > 0:
            coverage = (parse_success / parse_total * 100)
            print(f"Session parse coverage: {coverage:.1f}% ({parse_success}/{parse_total})")
        conn.close()
        await client.disconnect()
        print("Done.")

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
            print("\nBye!")
            break

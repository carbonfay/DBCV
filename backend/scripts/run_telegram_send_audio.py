"""Utility to manually run Telegram Send Audio integration without frontend."""
import argparse
import asyncio
import json
from uuid import UUID

from app.integrations.telegram.send_audio import TelegramSendAudioIntegration


class StaticCredentialsResolver:
    """Minimal credentials resolver that always returns provided bot token."""

    def __init__(self, bot_token: str):
        self._bot_token = bot_token

    async def get_default_for(self, **_: object) -> dict:
        return {"bot_token": self._bot_token}


class ConsoleLogger:
    """Simple logger with async interface expected by integrations."""

    async def info(self, message: str) -> None:
        print(f"[INFO] {message}")

    async def error(self, message: str) -> None:
        print(f"[ERROR] {message}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run Telegram Send Audio integration manually."
    )
    parser.add_argument("--bot-token", required=True, help="Telegram bot token")
    parser.add_argument("--chat-id", required=True, help="Target chat ID")
    parser.add_argument(
        "--audio-file-id",
        help="Existing Telegram file_id. Use this OR --audio-url.",
    )
    parser.add_argument(
        "--audio-url",
        help="Direct URL/path to audio file. Use this OR --audio-file-id.",
    )
    parser.add_argument("--caption", help="Caption text", default=None)
    parser.add_argument("--parse-mode", choices=["HTML", "Markdown", "MarkdownV2"])
    parser.add_argument("--title", help="Track title")
    parser.add_argument("--performer", help="Track performer")
    parser.add_argument(
        "--duration",
        type=int,
        help="Duration in seconds",
    )
    parser.add_argument(
        "--bot-id",
        default="00000000-0000-0000-0000-000000000000",
        help="Bot UUID (used only for logging/credentials).",
    )
    return parser.parse_args()


async def main() -> None:
    args = parse_args()

    if not args.audio_file_id and not args.audio_url:
        raise SystemExit("Provide --audio-file-id or --audio-url")

    integration = TelegramSendAudioIntegration()
    resolver = StaticCredentialsResolver(args.bot_token)
    logger = ConsoleLogger()

    config = {
        "chat_id": args.chat_id,
        "audio_file_id": args.audio_file_id,
        "audio_url": args.audio_url,
        "caption": args.caption,
        "parse_mode": args.parse_mode,
        "title": args.title,
        "performer": args.performer,
        "duration": args.duration,
    }

    result = await integration.execute(
        config=config,
        credentials_resolver=resolver,
        bot_id=UUID(args.bot_id),
        logger=logger,
    )

    print(json.dumps(result, ensure_ascii=False, indent=2, default=str))


if __name__ == "__main__":
    asyncio.run(main())


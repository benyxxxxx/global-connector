
import os, httpx
from typing import Optional

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
API = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}" if TELEGRAM_BOT_TOKEN else None

class TelegramClient:
    def __init__(self):
        if not API:
            raise RuntimeError("TELEGRAM_BOT_TOKEN not set")
        self.api = API

    async def send_message(self, chat_id: int | str, text: str, reply_to_message_id: Optional[int] = None):
        payload = {"chat_id": chat_id, "text": text, "parse_mode": "MarkdownV2"}
        if reply_to_message_id is not None:
            payload["reply_to_message_id"] = reply_to_message_id
        async with httpx.AsyncClient(timeout=10) as cx:
            r = await cx.post(f"{self.api}/sendMessage", json=payload)
            r.raise_for_status()
            return r.json()

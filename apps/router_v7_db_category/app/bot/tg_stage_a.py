import os
import time
import aiohttp
from aiogram import types
from aiogram.dispatcher import Dispatcher

INTEGRATOR_BASE_URL = os.environ.get("INTEGRATOR_BASE_URL", "http://localhost:8000")
ADMIN_HEADER_NAME   = "X-Integrator-Admin"
ADMIN_HEADER_VALUE  = os.environ.get("PROMOTE_ADMIN_TOKEN", "")

MAX_ZIP_BYTES = 60 * 1024 * 1024  # 60MB

def wire_stage_a(dp: Dispatcher, bot_token: str):
    @dp.message_handler(content_types=["document"])
    async def handle_zip(message: types.Message):
        doc = message.document
        if not doc:
            return
        if not doc.file_name.lower().endswith(".zip"):
            await message.reply("❌ Please send a .zip file.")
            return
        if doc.mime_type and doc.mime_type not in ("application/zip", "application/x-zip-compressed"):
            await message.reply("❌ File is not a ZIP.")
            return
        if doc.file_size and doc.file_size > MAX_ZIP_BYTES:
            await message.reply("❌ ZIP too large (max 60 MB).")
            return

        file = await dp.bot.get_file(doc.file_id)
        tg_url = f"https://api.telegram.org/file/bot{bot_token}/{file.file_path}"

        try:
            timeout = aiohttp.ClientTimeout(total=180, connect=10, sock_read=120)
            async with aiohttp.ClientSession(timeout=timeout) as sess:
                # Download from Telegram
                async with sess.get(tg_url) as r:
                    r.raise_for_status()
                    zip_bytes = await r.read()
                if len(zip_bytes) > MAX_ZIP_BYTES:
                    await message.reply("❌ ZIP too large (max 60 MB).")
                    return

                # Upload to Integrator
                data = aiohttp.FormData()
                data.add_field("file", zip_bytes, filename=doc.file_name, content_type="application/zip")
                data.add_field("title", f"tg-{message.from_user.username or 'user'}-{int(time.time())}")
                headers = {ADMIN_HEADER_NAME: ADMIN_HEADER_VALUE} if ADMIN_HEADER_VALUE else {}

                async with sess.post(f"{INTEGRATOR_BASE_URL}/integrations/stage-a/submit-zip",
                                     data=data, headers=headers) as resp:
                    if resp.status < 300:
                        j = await resp.json()
                        branch = j.get("branch", "(unknown)")
                        await message.reply(f"✅ Stage A uploaded\nBranch: {branch}")
                    else:
                        # show server's message so we see WHY it's 400/403/413
                        try:
                            body = await resp.text()
                        except Exception:
                            body = ""
                        preview = (body or "").strip()
                        if len(preview) > 400:
                            preview = preview[:400] + "…"
                        await message.reply(
                            f"❌ Stage A error {resp.status}."
                            + (f"\n{preview}" if preview else "")
                        )

        except Exception:
            await message.reply("❌ Stage A failed. Please try again.")

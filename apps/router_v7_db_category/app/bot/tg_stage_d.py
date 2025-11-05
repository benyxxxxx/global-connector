import os, aiohttp, time
from aiogram import types
from aiogram.dispatcher import Dispatcher

INTEGRATOR_BASE_URL = os.environ.get("INTEGRATOR_BASE_URL", "http://127.0.0.1:8080")
ADMIN_HEADER_NAME = "X-Integrator-Admin"
ADMIN_HEADER_VALUE = os.environ.get("PROMOTE_ADMIN_TOKEN", "")
MAX_BYTES = 500 * 1024

def wire_stage_d(dp: Dispatcher, bot_token: str):
    @dp.message_handler(content_types=["document"])
    async def handle_docs(message: types.Message):
        doc = message.document
        name = (doc.file_name or "").lower()
        if not any(name.endswith(ext) for ext in (".patch", ".diff", ".yaml", ".yml", ".json")):
            return # ignore other docs

        # download from Telegram
        file = await dp.bot.get_file(doc.file_id)
        tg_url = f"https://api.telegram.org/file/bot{bot_token}/{file.file_path}"
        timeout = aiohttp.ClientTimeout(total=180, connect=10, sock_read=120)
        async with aiohttp.ClientSession(timeout=timeout) as sess:
            async with sess.get(tg_url) as r:
                r.raise_for_status()
                data = await r.read()

        if len(data) > MAX_BYTES:
            await message.reply("❌ File too large (max 500KB).")
            return

        headers = {ADMIN_HEADER_NAME: ADMIN_HEADER_VALUE} if ADMIN_HEADER_VALUE else {}
        title = f"tg-{message.from_user.username or 'user'}-{int(time.time())}"
        dry = False
        if message.caption and "dryrun" in message.caption.lower():
            dry = True

        if name.endswith((".patch", ".diff")): # patch flow
            url = f"{INTEGRATOR_BASE_URL}/integrations/stage-d/{'dry-run' if dry else 'submit-patch'}"
            form = aiohttp.FormData()
            form.add_field("file", data, filename=doc.file_name, content_type="text/x-diff")
            form.add_field("title", title)
            if dry:
                form.add_field("kind", "patch")

            async with sess.post(url, data=form, headers=headers) as resp:
                if resp.status < 300:
                    j = await resp.json()
                    files = j.get("files", [])
                    await message.reply(
                        f"✅ Stage D {'dry-run ' if dry else ''}patch\n"
                        f"Branch: {j.get('branch')}\n"
                        f"Files: {', '.join(files) if files else '(none)'}"
                    )
                else:
                    await message.reply(f"❌ Stage D patch error {resp.status}.")
            return

        # spec flow (yaml/json)
        url = f"{INTEGRATOR_BASE_URL}/integrations/stage-d/{'dry-run' if dry else 'submit-edits'}"
        form = aiohttp.FormData()
        form.add_field("file", data, filename=doc.file_name,
                        content_type="application/x-yaml" if name.endswith(('.yaml', '.yml')) else "application/json")
        form.add_field("title", title)
        if dry:
            form.add_field("kind", "edits")

        async with sess.post(url, data=form, headers=headers) as resp:
            if resp.status < 300:
                j = await resp.json()
                files = j.get("files", [])
                await message.reply(
                    f"✅ Stage D {'dry-run ' if dry else ''}spec\n"
                    f"Branch: {j.get('branch')}\n"
                    f"Files: {', '.join(files) if files else '(none)'}"
                )
            else:
                await message.reply(f"❌ Stage D spec error {resp.status}.")
import os, re
import aiohttp
from aiogram import types
from aiogram.dispatcher import Dispatcher

INTEGRATOR_BASE_URL = os.environ.get("INTEGRATOR_BASE_URL", "http://localhost:8000")
ADMIN_HEADER_NAME   = "X-Integrator-Admin"
ADMIN_HEADER_VALUE  = os.environ.get("PROMOTE_ADMIN_TOKEN", "")

BR_RE = re.compile(r"^stage-a/[a-z0-9._/-]{1,60}$")

def wire_stage_b(dp: Dispatcher):
    @dp.message_handler(commands=["promote"])
    async def promote_cmd(message: types.Message):
        branch = message.get_args().strip()
        if not branch:
            await message.reply("Usage: /promote stage-a/<branch>")
            return
        if not BR_RE.match(branch):
            await message.reply("❌ Invalid branch. Expected: stage-a/<slug>")
            return

        headers = {ADMIN_HEADER_NAME: ADMIN_HEADER_VALUE} if ADMIN_HEADER_VALUE else {}
        try:
            timeout = aiohttp.ClientTimeout(total=90, connect=10, sock_read=60)
            async with aiohttp.ClientSession(timeout=timeout) as sess:
                async with sess.post(
                    f"{INTEGRATOR_BASE_URL}/integrations/stage-b/promote",
                    json={"branch": branch},
                    headers=headers,
                ) as resp:
                    # try to parse JSON (backend sends reasons on 409)
                    try:
                        j = await resp.json()
                    except Exception:
                        j = {}

                    if resp.status < 300 and j.get("ok", True):
                        await message.reply(
                            "✅ Promoted\n"
                            f"PR: #{j.get('pr_number')} | Tag: {j.get('tag')}\n"
                            f"SHA: {j.get('sha')}\n{j.get('pr_url')}"
                        )
                    elif resp.status == 409 or j.get("ok") is False:
                        # show a human reason + PR link
                        reason = j.get("reason", "Merge is blocked (checks/review/conflicts).")
                        pr_url = j.get("pr_url", "")
                        text = f"❌ Promote blocked\n{reason}"
                        if pr_url:
                            text += f"\n{pr_url}"
                        await message.reply(text)
                    else:
                        # fallback: include short server body preview
                        try:
                            body = await resp.text()
                        except Exception:
                            body = ""
                        preview = (body or "").strip()
                        if len(preview) > 400:
                            preview = preview[:400] + "…"
                        await message.reply(
                            f"❌ Promote error {resp.status}."
                            + (f"\n{preview}" if preview else "")
                        )
        except Exception:
            await message.reply("❌ Promote failed. Please try again.")

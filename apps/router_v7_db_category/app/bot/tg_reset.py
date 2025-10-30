import os
from aiogram import types
from aiogram.dispatcher import Dispatcher
from app.services.github_service import trigger_deployment_workflow

ADMIN_IDS = [int(i) for i in os.environ.get("BOT_ADMIN_IDS", "").split(",") if i]

def wire_reset_command(dp: Dispatcher):
    @dp.message_handler(commands=['resetbot'])
    async def handle_reset_command(message: types.Message):
        if message.from_user.id not in ADMIN_IDS:
            return await message.reply("🚫 You are not authorized for this command.")

        args = message.get_args().strip().split()
        fly_config = args[0] if args else "fly.test.toml"
        
        await message.reply(f"🚀 Triggering deployment with `{fly_config}`...")
        run_url = await trigger_deployment_workflow(fly_config=fly_config)

        if run_url:
            await message.reply(f"✅ Workflow started. Track progress here:\n{run_url}", disable_web_page_preview=True)
        else:
            await message.reply("❌ Failed to trigger deployment. Check bot logs.")
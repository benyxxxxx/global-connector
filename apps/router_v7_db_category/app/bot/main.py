# app/bot/main.py
import os
from aiogram import Bot, Dispatcher, types
from aiogram.utils import executor

from bot.tg_stage_a import wire_stage_a
from bot.tg_stage_b import wire_stage_b
from bot.commands_public import PUBLIC_COMMANDS
from bot.tg_stage_d import wire_stage_d
from bot.tg_reset import wire_reset_command

# 1. Get the token first
BOT_TOKEN = os.environ.get("BOT_TOKEN")
if not BOT_TOKEN:
    raise RuntimeError("BOT_TOKEN env var is required")

# 2. Create Bot and Dispatcher instances
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(bot)

# 3. Now, wire up all your command handlers to the dispatcher
wire_stage_a(dp, BOT_TOKEN)
wire_stage_b(dp)
wire_stage_d(dp, BOT_TOKEN)
wire_reset_command(dp) # Make sure this file exists

# --- Define your message handlers ---
@dp.message_handler(commands=["start"])
async def _start(msg: types.Message):
    await msg.reply(
        "Send a .zip to create a Stage A branch.\n"
        "Promote with: /promote stage-a/<branch>\n"
        "Stage C (release & verify) runs automatically on release/* tags."
    )

@dp.message_handler(commands=["help"])
async def _help(msg: types.Message):
    await msg.reply(
        "• Stage A: send a .zip\n"
        "• Stage B: /promote stage-a/<branch>\n"
        "• Stage C: auto on release/* tag\n"
        "Hidden commands aren’t in the menu—type them directly."
    )

async def on_startup(_):
    await bot.set_my_commands(PUBLIC_COMMANDS)

# 4. Start the bot
if __name__ == "__main__":
    executor.start_polling(dp, skip_updates=True, on_startup=on_startup)
import os
from aiogram import Bot, Dispatcher
from .tg_stage_a import wire_stage_a
from .tg_stage_b import wire_stage_b
from .tg_stage_d import wire_stage_d
from .tg_reset import wire_reset_command
from .commands_public import PUBLIC_COMMANDS

# Get token and ensure it exists
BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
if not BOT_TOKEN:
    raise RuntimeError("BOT_TOKEN env var is not set")

# Create the single bot and dispatcher instances
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(bot)

# Wire up all command handlers to this single dispatcher
wire_stage_a(dp, BOT_TOKEN)
wire_stage_b(dp)
wire_stage_d(dp, BOT_TOKEN)
wire_reset_command(dp)

# Define startup tasks
async def on_startup(_):
    await bot.set_my_commands(PUBLIC_COMMANDS)

# Define shutdown tasks
async def on_shutdown(_):
    await bot.delete_webhook()
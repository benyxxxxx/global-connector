from aiogram import types

PUBLIC_COMMANDS = [
    types.BotCommand(command="/start", description="Start the bot"),
    types.BotCommand(command="/help", description="Show help message"),
    types.BotCommand(command="/promote", description="Promote a Stage A branch to Stage B"),
]
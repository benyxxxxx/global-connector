import os
import httpx

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
SET_COMMANDS_URL = f"https://api.telegram.org/bot{BOT_TOKEN}/setMyCommands"

# ✅ Define Telegram bot commands with syntax help
commands = [
    {"command": "createagent", "description": "Create a new agent"},
    {"command": "listagent", "description": "List all your agents"},
    {"command": "editagent", "description": "Edit agent (/editagent = <agent name>)"},
    {"command": "useagent", "description": "Use agent (/useagent = <agent name>)"},
    {"command": "deleteagent", "description": "Delete agent (/deleteagent = <agent name>)"},
]

async def set_bot_commands():
    async with httpx.AsyncClient() as client:
        response = await client.post(SET_COMMANDS_URL, json={"commands": commands})
        print("✅ Bot command set status:", response.json())

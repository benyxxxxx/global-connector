import os
import httpx
from fastapi import FastAPI, Request
from openai import OpenAI
from typing import Dict
from set_commands import set_bot_commands

TELEGRAM_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_API_URL = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
OPENROUTER_SITE_URL = os.getenv("OPENROUTER_SITE_URL", "")
OPENROUTER_SITE_NAME = os.getenv("OPENROUTER_SITE_NAME", "")

client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=OPENROUTER_API_KEY,
)
TELEGRAM_WEBHOOK_URL = os.getenv("WEBHOOK_URL", "https://assistant-bot-dev.fly.dev/webhook")

app = FastAPI()

async def set_telegram_webhook():
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/setWebhook"
    async with httpx.AsyncClient() as client:
        res = await client.post(url, params={"url": TELEGRAM_WEBHOOK_URL})
        print("✅ Webhook set:", res.json())

@app.on_event("startup")
async def startup():
    await set_bot_commands()
    await set_telegram_webhook()
    print("✅ Bot commands set successfully.")

# In-memory store
AGENTS: Dict[str, Dict] = {}
USER_SESSIONS: Dict[int, Dict] = {}

async def send_telegram_message(chat_id: int, text: str):
    async with httpx.AsyncClient() as client:
        await client.post(TELEGRAM_API_URL, json={"chat_id": chat_id, "text": text})

async def ask_openai(prompt: str, system_prompt: str = "") -> str:
    try:
        completion = client.chat.completions.create(
            model="openai/gpt-4o-mini",
            extra_headers={
                "HTTP-Referer": OPENROUTER_SITE_URL,
                "X-Title": OPENROUTER_SITE_NAME,
            },
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt}
            ]
        )
        return completion.choices[0].message.content
    except Exception as e:
        print(f"❌ OpenAI request failed: {e}")
        return "⚠️ Failed to get response from the agent."

@app.post("/webhook")
async def telegram_webhook(request: Request):
    data = await request.json()
    message = data.get("message")
    if not message or "text" not in message:
        return {"status": "ignored"}

    chat_id = message["chat"]["id"]
    user_id = message["from"]["id"]
    text = message["text"].strip()

    session = USER_SESSIONS.get(user_id)

    # === COMMANDS: always checked FIRST ===
    if text.startswith("/createagent"):
        USER_SESSIONS[user_id] = {"state": "create_name"}
        await send_telegram_message(chat_id, "🆕 Enter agent name:")
        return {"status": "ok"}

    if text.startswith("/editagent"):
        parts = text.split("=", 1)
        if len(parts) != 2:
            await send_telegram_message(chat_id, "❌ Please provide agent name like `/editagent = My Agent`")
            return {"status": "ok"}
        agent_name = parts[1].strip()
        agent = AGENTS.get(agent_name)
        if not agent:
            await send_telegram_message(chat_id, f"❌ Agent '{agent_name}' not found.")
            return {"status": "ok"}
        if agent["owner_id"] != user_id:
            await send_telegram_message(chat_id, "❌ You are not the owner of this agent.")
            return {"status": "ok"}
        USER_SESSIONS[user_id] = {"state": "edit_name", "agent_name": agent_name}
        await send_telegram_message(chat_id, f"✏️ Editing '{agent_name}'. Enter new name (or send the same):")
        return {"status": "ok"}

    if text.startswith("/deleteagent"):
        parts = text.split("=", 1)
        if len(parts) != 2:
            await send_telegram_message(chat_id, "❌ Please provide agent name like `/deleteagent = My Agent`")
            return {"status": "ok"}
        agent_name = parts[1].strip()
        agent = AGENTS.get(agent_name)
        if not agent:
            await send_telegram_message(chat_id, f"❌ Agent '{agent_name}' not found.")
            return {"status": "ok"}
        if agent["owner_id"] != user_id:
            await send_telegram_message(chat_id, "❌ You are not the owner of this agent.")
            return {"status": "ok"}
        AGENTS.pop(agent_name)
        # Clear session if user was interacting with this agent
        if session and session.get("agent_name") == agent_name:
            USER_SESSIONS.pop(user_id, None)
        await send_telegram_message(chat_id, f"🗑️ Agent '{agent_name}' deleted.")
        return {"status": "ok"}

    if text.startswith("/listagent"):
        visible_agents = [
            f"🔹 *{name}*\n📝 {details['description']}\n🔒 {'Private' if details['is_private'] else 'Public'}"
            for name, details in AGENTS.items()
            if not details["is_private"] or details["owner_id"] == user_id
        ]
        response = "\n\n".join(visible_agents) if visible_agents else "No agents available."
        await send_telegram_message(chat_id, response)
        return {"status": "ok"}

    if text.startswith("/useagent"):
        parts = text.split("=", 1)
        if len(parts) != 2:
            await send_telegram_message(chat_id, "❌ Please provide agent name like `/useagent = My Agent`")
            return {"status": "ok"}
        agent_name = parts[1].strip()
        agent = AGENTS.get(agent_name)
        if not agent:
            await send_telegram_message(chat_id, f"❌ Agent '{agent_name}' not found.")
            return {"status": "ok"}
        if agent["is_private"] and agent["owner_id"] != user_id:
            await send_telegram_message(chat_id, "🔒 This agent is private.")
            return {"status": "ok"}
        USER_SESSIONS[user_id] = {"state": "using_agent", "agent_name": agent_name}
        await send_telegram_message(chat_id, f"✅ Now chatting with '{agent_name}'. Ask me anything!")
        return {"status": "ok"}

    # === NO COMMANDS FOUND: HANDLE SESSION STATE ===
    if session:
        state = session.get("state")

        # Create agent flow
        if state == "create_name":
            session["agent_name"] = text
            session["state"] = "create_description"
            await send_telegram_message(chat_id, "📝 Enter agent description:")
            return {"status": "ok"}

        if state == "create_description":
            session["agent_description"] = text
            session["state"] = "create_privacy"
            await send_telegram_message(chat_id, "🔒 Should this agent be private? (yes/no):")
            return {"status": "ok"}

        if state == "create_privacy":
            is_private = text.lower() in ["yes", "true", "1"]
            name = session["agent_name"]
            AGENTS[name] = {
                "description": session["agent_description"],
                "is_private": is_private,
                "owner_id": user_id
            }
            USER_SESSIONS.pop(user_id, None)
            await send_telegram_message(chat_id, f"✅ Agent '{name}' created.")
            return {"status": "ok"}

        # Edit agent flow
        if state == "edit_name":
            session["new_name"] = text
            session["state"] = "edit_description"
            await send_telegram_message(chat_id, "📝 Enter new description:")
            return {"status": "ok"}

        if state == "edit_description":
            session["new_description"] = text
            session["state"] = "edit_privacy"
            await send_telegram_message(chat_id, "🔒 Should this agent be private? (yes/no):")
            return {"status": "ok"}

        if state == "edit_privacy":
            is_private = text.lower() in ["yes", "true", "1"]
            old_name = session["agent_name"]
            new_name = session.get("new_name", old_name)
            # Rename if changed
            if new_name != old_name:
                agent_data = AGENTS.pop(old_name)
                AGENTS[new_name] = agent_data
            AGENTS[new_name]["description"] = session.get("new_description", AGENTS[new_name]["description"])
            AGENTS[new_name]["is_private"] = is_private
            AGENTS[new_name]["owner_id"] = user_id  # just to be sure
            USER_SESSIONS.pop(user_id, None)
            await send_telegram_message(chat_id, f"✅ Agent '{new_name}' updated.")
            return {"status": "ok"}

        # Using agent chat flow
        if state == "using_agent":
            agent_name = session["agent_name"]
            agent = AGENTS.get(agent_name)
            if not agent:
                await send_telegram_message(chat_id, "❌ Agent not found.")
                return {"status": "ok"}
            reply = await ask_openai(prompt=text, system_prompt=agent["description"])
            await send_telegram_message(chat_id, reply)
            return {"status": "ok"}

    # Default fallback
    await send_telegram_message(chat_id, "🤖 Unrecognized command. Type `/` to see available actions.")
    return {"status": "ok"}

@app.get("/")
def root():
    return {"message": "Bot is running. Set webhook to /webhook"}

import os
import time
import httpx

import uvicorn
from core.agents.coordinator import Coordinator
from core.service import AgentRunner
from fastapi import (
    APIRouter,
    FastAPI,
    Request
)
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from config import get_logger
from routers.data_model import ServiceBotRequest

current_time = time.strftime("%Y-%m-%d %H:%M:%S")

current_location = "Hanoi, Vietnam"
logger = get_logger()

app = FastAPI(title="Service Bot API", version="1.0.0")
router = APIRouter(prefix="/api")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)
# router = APIRouter(prefix="/api")

logger = get_logger()

# Initialize your agent only once
coordinator_agent = Coordinator(current_time, current_location).get_agent()
agent_runner = AgentRunner(agent=coordinator_agent)

TELEGRAM_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_API_URL = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}"

@router.post("/service_bot")
async def service_bot(service_bot_request: ServiceBotRequest) -> JSONResponse:
    """Service bot endpoint to handle user requests.

    Parameters
    ----------
    service_bot_request : ServiceBotRequest
        The request data containing user message, user ID, and session ID.

    Returns
    -------
    JSONResponse
        A JSON response containing the status and response from the agent.
    """
    user_id = service_bot_request.user_id
    session_id = service_bot_request.request_id
    user_message = service_bot_request.user_message
    logger.info(f"Received message from user {user_id}: {user_message}")
    logger.info(f"User ID: {user_id}")
    logger.info(f"Session ID: {session_id}")

    try:
        current_session = await agent_runner.get_session(
            user_id=user_id, session_id=session_id
        )
        if not current_session:
            logger.info(
                f"Creating new session for user {user_id} \
                with session ID {session_id}"
            )
            await agent_runner.create_session(user_id, session_id)

        response = await agent_runner.call_agent_async(
            user_message, user_id, session_id
        )
        logger.info(f"Processed message from user {user_id}: {user_message}")
        return {"status": "success", "response": response}

    except Exception as e:
        logger.error(f"Error processing update: {e}")
        return {"status": "error", "detail": str(e)}


@router.get("/")
def health_check() -> JSONResponse:
    """Health check endpoint.

    Returns
    -------
    JSONResponse
        A JSON response indicating that the service bot is running.
    """
    return {"message": "Service bot is running!"}



BOT_USERNAME = "danang_connector_bot"

@app.post("/telegram-webhook")
async def telegram_webhook(request: Request):
    try:
        data = await request.json()
        message = data.get("message", {})
        text = message.get("text", "")
        chat = message.get("chat", {})
        user = message.get("from", {})
        reply_to = message.get("reply_to_message", {})

        chat_id = chat.get("id")
        chat_type = chat.get("type")  # "private", "group", "supergroup"
        user_id = str(user.get("id"))
        message_id = message.get("message_id")
        session_id = user_id

        if not text or not chat_id or not user_id:
            return {"status": "ignored"}

        text_lower = text.lower()
        first_words = text_lower.strip().split()[:3]
        is_private = chat_type == "private"
        is_reply_to_bot = reply_to.get("from", {}).get("is_bot", False)
        mentions_trigger = any(word in {"bot", "ai"} for word in first_words)
        mentions_bot_username = f"@{BOT_USERNAME.lower()}" in text_lower

        if not is_private and not (is_reply_to_bot or mentions_trigger or mentions_bot_username):
            return {"status": "ignored"}

        logger.info(f"📥 From {user_id}: {text}")

        if not await agent_runner.get_session(user_id, session_id):
            await agent_runner.create_session(user_id, session_id)
            logger.info(f"🆕 Created session for {user_id}")

        async with httpx.AsyncClient() as client:
            await client.post(
                f"{TELEGRAM_API_URL}/sendChatAction",
                json={"chat_id": chat_id, "action": "typing"}
            )

            try:
                response = await agent_runner.call_agent_async(text, user_id, session_id)
            except Exception as e:
                response = str(e)
                

            await client.post(
                f"{TELEGRAM_API_URL}/sendMessage",
                json={
                    "chat_id": chat_id,
                    "text": response or "🤖 Sorry, I didn’t understand that.",
                    "reply_to_message_id": message_id,
                    "parse_mode": "Markdown",
                },
            )

        logger.info(f"✅ Replied to {user_id}")
        return {"status": "success"}

    except Exception as e:
        logger.exception(f"❌ Error in Telegram webhook {e}")
        return {"status": "error", "detail": str(e)}



def main():
    """Main function to run the FastAPI application using Uvicorn."""
    uvicorn.run(
        app,
        host=str(os.getenv("SERVICE_BOT_HOST")),
        port=int(os.getenv("SERVICE_BOT_PORT")),
    )


app.include_router(router)

if __name__ == "__main__":
    main()

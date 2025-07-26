import asyncio
import time

from core.agents.coordinator import Coordinator
from core.service import AgentRunner

from config import Config, get_logger

current_time = time.strftime("%Y-%m-%d %H:%M:%S")
current_location = "Hanoi, Vietnam"

logger = get_logger()


async def main():
    """
    Main function to run the agent interaction loop.
    """
    coordinator_agent = Coordinator(current_time, current_location).get_agent()
    agent_runner = AgentRunner(agent=coordinator_agent)

    user_id = Config.USER_ID
    session_id = Config.SESSION_ID

    logger.info(
        f"Creating session for user {user_id} with session ID {session_id}"
    )
    await agent_runner.create_session(user_id, session_id)

    while True:
        user_query = input("Enter your query (or 'exit' to quit): ")
        if user_query.lower() == "exit":
            logger.info("Exiting the agent interaction loop.")
            break
        await agent_runner.call_agent_async(user_query, user_id, session_id)


if __name__ == "__main__":
    asyncio.run(main())

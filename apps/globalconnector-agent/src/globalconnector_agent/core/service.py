from google.adk.runners import Runner
from google.adk.sessions import DatabaseSessionService
from google.genai import types

from config import Config, get_logger

logger = get_logger()


class AgentRunner:
    """
    Manages the execution of the agent and session interactions.
    """

    def __init__(
        self,
        agent,
        app_name: str = "my_app",
        events_history_limit: int = 30,
    ):
        self.agent = agent
        self.app_name = app_name
        self.events_history_limit = events_history_limit
        self.session_service = DatabaseSessionService(
            db_url=f"sqlite:///{Config.CHAT_HISTORY_DB_PATH}",
        )
        self.runner = Runner(
            agent=self.agent,
            app_name=self.app_name,
            session_service=self.session_service,
        )

    async def get_session(self, user_id, session_id):
        session = await self.session_service.get_session(
            app_name=self.app_name, user_id=user_id, session_id=session_id
        )
        if not session:
            logger.error(
                f"Session not found: App='{self.app_name}', "
                f"User='{user_id}', Session='{session_id}'"
            )
            return None
        logger.info(
            f"Session retrieved: App='{self.app_name}', "
            f"User='{user_id}', Session='{session_id}'"
        )
        session.events = session.events[-self.events_history_limit :]
        return session

    async def create_session(self, user_id, session_id):
        session = await self.session_service.create_session(
            app_name=self.app_name, user_id=user_id, session_id=session_id
        )
        logger.info(
            f"Session created: App='{self.app_name}', "
            f"User='{user_id}', Session='{session_id}'"
        )
        return session

    async def call_agent_async(self, query, user_id, session_id):
        logger.info(f"\n>>> User Query: {query}")
        content = types.Content(role="user", parts=[types.Part(text=query)])
        final_response_text = "Agent did not produce a final response."

        async for event in self.runner.run_async(
            user_id=user_id, session_id=session_id, new_message=content
        ):
            if event.is_final_response():
                if event.content and event.content.parts:
                    final_response_text = event.content.parts[0].text
                elif event.actions and event.actions.escalate:
                    final_response_text = (
                        f"Agent escalated: "
                        f"{event.error_message or 'No specific message.'}"
                    )
                break

        logger.info(f"<<< Agent Response: {final_response_text}")
        return final_response_text

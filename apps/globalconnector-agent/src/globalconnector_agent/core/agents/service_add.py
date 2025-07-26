from core.agents.base import BaseAgent
from core.prompts import SERVICE_ADDING_AGENT_PROMPT
from google.adk.agents import LlmAgent
from core.tools.services import services_add_tool
from config import Config


class ServiceAddingAgent(BaseAgent):
    """Agent for handling service adding."""

    def __init__(self, current_time: str, current_location: str):
        self.current_time = current_time
        self.current_location = current_location

    def get_agent(self):
        prompt = SERVICE_ADDING_AGENT_PROMPT.format(
            current_time=self.current_time,
            current_location=self.current_location,
        )
        return LlmAgent(
            name="ServiceAdding",
            description="Agent for handling service additions",
            model=Config.DEFAULT_MODEL,
            instruction=prompt,
            tools=[services_add_tool],
        )

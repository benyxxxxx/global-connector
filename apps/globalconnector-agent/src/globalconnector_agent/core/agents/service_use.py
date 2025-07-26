from core.agents.base import BaseAgent
from core.prompts import SERVICE_USING_AGENT_PROMPT
from core.tools.services import services_list_tool
from google.adk.agents import LlmAgent

from config import Config


class ServiceUsingAgent(BaseAgent):
    """Agent for handling service using."""

    def __init__(self, current_time: str, current_location: str):
        self.current_time = current_time
        self.current_location = current_location

    def get_agent(self):
        prompt = SERVICE_USING_AGENT_PROMPT.format(
            current_time=self.current_time,
            current_location=self.current_location,
        )
        return LlmAgent(
            name="ServiceUsing",
            description="Agent for handling service usage",
            model=Config.DEFAULT_MODEL,
            instruction=prompt,
            tools=[services_list_tool],
        )

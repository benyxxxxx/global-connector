from core.agents.base import BaseAgent
from core.prompts import PRICES_AGENT_PROMPT
from core.tools.prices import prices_list_tool
from google.adk.agents import LlmAgent

from config import Config


class PricesAgent(BaseAgent):
    """Agent for handling price information."""

    def __init__(self, current_time: str, current_location: str):
        self.current_time = current_time
        self.current_location = current_location

    def get_agent(self):
        prompt = PRICES_AGENT_PROMPT.format(
            current_time=self.current_time,
            current_location=self.current_location,
        )
        return LlmAgent(
            name="Prices",
            description="Agent for handling price information",
            model=Config.DEFAULT_MODEL,
            instruction=prompt,
            tools=[prices_list_tool],
        )

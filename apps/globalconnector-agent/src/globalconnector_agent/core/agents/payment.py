from core.agents.base import BaseAgent
from core.prompts import PAYMENT_AGENT_PROMPT
from core.tools.payment import payment_tool
from google.adk.agents import LlmAgent

from config import Config


class PaymentAgent(BaseAgent):
    """Agent for handling payments."""

    def __init__(self, current_time: str, current_location: str):
        self.current_time = current_time
        self.current_location = current_location

    def get_agent(self):
        prompt = PAYMENT_AGENT_PROMPT.format(
            current_time=self.current_time,
            current_location=self.current_location,
        )
        return LlmAgent(
            name="Payment",
            description="Agent for handling payment queries and issues",
            model=Config.DEFAULT_MODEL,
            instruction=prompt,
            tools=[payment_tool],
        )

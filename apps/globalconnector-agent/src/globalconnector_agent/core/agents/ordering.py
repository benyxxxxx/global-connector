from core.agents.base import BaseAgent
from core.prompts import ORDERING_AGENT_PROMPT
from core.tools.ordering import (
    list_nearby_restaurants_tool,
    order_food_tool,
    track_ordered_food_tool,
)
from google.adk.agents import LlmAgent

from config import Config


class OrderingAgent(BaseAgent):
    """Agent for ordering and tracking food delivery."""

    def __init__(self, current_time: str, current_location: str):
        self.current_time = current_time
        self.current_location = current_location

    def get_agent(self):
        prompt = ORDERING_AGENT_PROMPT.format(
            current_time=self.current_time,
            current_location=self.current_location,
        )
        return LlmAgent(
            name="Ordering",
            description="Agent for ordering and tracking delivery of food",
            instruction=prompt,
            model=Config.DEFAULT_MODEL,
            tools=[
                order_food_tool,
                list_nearby_restaurants_tool,
                track_ordered_food_tool,
            ],
        )

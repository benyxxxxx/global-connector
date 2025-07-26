from core.agents.base import BaseAgent
from core.prompts import BOOKING_AGENT_PROMPT
from core.tools.booking import (
    book_hotel_tool,
    list_nearby_hotels_tool,
)
from google.adk.agents import LlmAgent

from config import Config


class BookingAgent(BaseAgent):
    """Agent for booking hotels."""

    def __init__(self, current_time: str, current_location: str):
        self.current_time = current_time
        self.current_location = current_location

    def get_agent(self):
        """
        Gets the configured Booking Agent.

        Returns
        -------
        LlmAgent
            An instance of the LlmAgent for booking.
        """
        prompt = BOOKING_AGENT_PROMPT.format(
            current_time=self.current_time,
            current_location=self.current_location,
        )
        return LlmAgent(
            name="Booking",
            description="Agent for booking hotels",
            instruction=prompt,
            model=Config.DEFAULT_MODEL,
            tools=[book_hotel_tool, list_nearby_hotels_tool],
        )

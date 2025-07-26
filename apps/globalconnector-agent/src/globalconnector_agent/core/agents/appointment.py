from core.agents.base import BaseAgent
from core.prompts import APPOINTMENT_AGENT_PROMPT
from core.tools.appointment import appointment_tool, list_services_tool
from google.adk.agents import LlmAgent

from config import Config


class AppointmentAgent(BaseAgent):
    """Agent for booking appointments."""

    def __init__(self, current_time: str, current_location: str):
        self.current_time = current_time
        self.current_location = current_location

    def get_agent(self):
        prompt = APPOINTMENT_AGENT_PROMPT.format(
            current_time=self.current_time,
            current_location=self.current_location,
        )
        return LlmAgent(
            name="Appointment",
            description="Agent for booking appointments",
            instruction=prompt,
            model=Config.DEFAULT_MODEL,
            tools=[appointment_tool, list_services_tool],
        )

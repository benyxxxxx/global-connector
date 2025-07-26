from core.agents.appointment import AppointmentAgent
from core.agents.base import BaseAgent
from core.agents.booking import BookingAgent
from core.agents.ordering import OrderingAgent
from core.agents.payment import PaymentAgent
from core.agents.prices import PricesAgent
from core.agents.service_add import ServiceAddingAgent
from core.agents.service_use import ServiceUsingAgent
from core.prompts import COORDINATOR_PROMPT
from google.adk.agents import LlmAgent

from config import Config


class Coordinator(BaseAgent):
    """Main coordinator agent to route tasks."""

    def __init__(self, current_time: str, current_location: str):
        self.current_time = current_time
        self.current_location = current_location

    def get_agent(self):
        prompt = COORDINATOR_PROMPT.format(
            current_time=self.current_time,
            current_location=self.current_location,
        )
        return LlmAgent(
            name="Coordinator",
            model=Config.DEFAULT_MODEL,
            instruction=prompt,
            description="Main coordinator/router.",
            sub_agents=[
                BookingAgent(
                    self.current_time, self.current_location
                ).get_agent(),
                PaymentAgent(
                    self.current_time, self.current_location
                ).get_agent(),
                OrderingAgent(
                    self.current_time, self.current_location
                ).get_agent(),
                AppointmentAgent(
                    self.current_time, self.current_location
                ).get_agent(),
                PricesAgent(
                    self.current_time, self.current_location
                ).get_agent(),
                ServiceAddingAgent(
                    self.current_time, self.current_location
                ).get_agent(),
                ServiceUsingAgent(
                    self.current_time, self.current_location
                ).get_agent(),
            ],
        )

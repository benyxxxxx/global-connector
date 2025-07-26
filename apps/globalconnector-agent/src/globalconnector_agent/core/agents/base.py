from abc import ABC, abstractmethod


class BaseAgent(ABC):
    """Abstract base class for all agents."""

    @abstractmethod
    def get_agent(self):
        """
        Returns the configured agent instance.

        Returns
        -------
        LlmAgent
            An instance of the LlmAgent.
        """
        pass

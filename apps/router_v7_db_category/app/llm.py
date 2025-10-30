import os
import logging
from typing import Any, Dict, List, Optional
import openai

logger = logging.getLogger(__name__)

class LLMClient:
    def __init__(self, model_name: Optional[str] = None, temperature: Optional[float] = None):
        self.model_name = model_name or os.getenv("LLM_MODEL", "openai/gpt-4o-mini")
        self.temperature = temperature if temperature is not None else float(os.getenv("LLM_TEMPERATURE", 0.7))
        self.client = None

        # --- START CORRECTION ---
        # Check for the presence of the OPENROUTER_API_KEY environment variable
        # to determine which client to use.
        if os.getenv("OPENROUTER_API_KEY"):
            logger.info("Using OpenRouter client.")
            self.client = openai.AsyncOpenAI(
                base_url=os.getenv("OPENROUTER_SITE_URL"),
                api_key=os.getenv("OPENROUTER_API_KEY"),
            )
        else:
            logger.info("Using OpenAI client.")
            self.client = openai.AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        # --- END CORRECTION ---

    async def get_agent_response(self, messages: List[Dict[str, Any]], tools: Optional[List[Dict[str, Any]]] = None) -> Any:
        if not self.client:
            raise ValueError("LLM client not initialized")
        try:
            response = await self.client.chat.completions.create(
                model=self.model_name,
                messages=messages,
                tools=tools,
                temperature=self.temperature,
            )
            return response.choices[0].message
        except Exception as e:
            logger.exception("Error getting LLM response: %s", e)
            return f"Error: {e}"
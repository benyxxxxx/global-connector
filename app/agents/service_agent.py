from __future__ import annotations
from typing import Tuple, Dict, Any, List
import json
from decimal import Decimal
from pathlib import Path

from app.clients import backend_api as be
from app.llm import LLMClient

# In-memory chat history for simplicity in this MVP
CHAT_HISTORY: Dict[str, List[Dict]] = {}

# Load the main agent prompt
try:
    PROMPT_PATH = Path(__file__).parent.parent / "prompts" / "orchestrator_prompt.txt"
    AGENT_PROMPT = PROMPT_PATH.read_text(encoding="utf-8")
except FileNotFoundError:
    print("ERROR: orchestrator_prompt.txt not found.")
    AGENT_PROMPT = "You are a helpful assistant."

# --- Tool Definitions ---
TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "browse_services",
            "description": "Use this tool to show public services the user can book or explore. If they mention a type (e.g. 'massage'), extract a short keyword.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "A search query keyword, e.g., 'pizza', 'tour', 'sim card'",
                    },
                },
                "required": [],
            },
        }
    }
]

# Map tool names to the functions that execute them
AVAILABLE_TOOLS = {
    "browse_services": be.list_services,
}

# Helper class to format JSON with Decimal types from the backend
class DecimalEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, Decimal):
            return str(obj)
        return super(DecimalEncoder, self).default(obj)

async def handle_message(user_id: str, text: str, channel: str = "http") -> Tuple[bool, str]:
    """
    This function now runs the main agent loop.
    """
    llm_client = LLMClient()
    
    messages = CHAT_HISTORY.setdefault(user_id, [
        {"role": "system", "content": AGENT_PROMPT}
    ])
    messages.append({"role": "user", "content": text})

    llm_response = await llm_client.get_agent_response(messages, TOOLS)
    messages.append(llm_response)

    # CORRECTED: Safely check for tool_calls attribute
    tool_calls = getattr(llm_response, 'tool_calls', None)
    
    if tool_calls:
        tool_call = tool_calls[0]
        tool_name = tool_call.function.name
        
        if tool_name in AVAILABLE_TOOLS:
            tool_function = AVAILABLE_TOOLS[tool_name]
            tool_args = json.loads(tool_call.function.arguments)
            
            print(f"--- Calling Tool: {tool_name} with args: {tool_args} ---")
            
            try:
                tool_result = await tool_function(user_id=user_id, **tool_args)
                
                messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "name": tool_name,
                    "content": json.dumps(tool_result, cls=DecimalEncoder),
                })
                
                final_response = await llm_client.get_agent_response(messages, TOOLS)
                messages.append(final_response)
                return True, final_response.content
            
            except Exception as e:
                # If the tool fails, inform the user and log the error
                print(f"--- Tool Error: {e} ---")
                return True, "Sorry, there was an error while trying to fetch that information."

    # If the LLM didn't call a tool, return its message directly
    return True, getattr(llm_response, 'content', "I'm not sure how to respond to that.")
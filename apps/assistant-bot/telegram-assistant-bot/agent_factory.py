#!/usr/bin/env python3
"""
Agent Factory for Aiogram Bot - handles different agent types and OpenAI integration
"""

import logging
from typing import Dict, Optional, List
import aiohttp
import json

logger = logging.getLogger(__name__)


class AgentFactory:
    """Factory class to manage different types of AI agents"""
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.openai_url = "https://api.openai.com/v1/chat/completions"
        
        # In-memory storage (replace with database in production)
        self.user_agents: Dict[int, str] = {}  # user_id -> agent_type
        self.user_contexts: Dict[int, List[dict]] = {}  # user_id -> conversation history
        
        self.SHARED_AGENT = "shared"
        self.PERSONAL_AGENT = "personal"
    
    async def create_agent_response(self, prompt: str, user_id: int) -> str:
        """Create a response using the appropriate agent for the user"""
        
        # Determine which agent to use
        agent_type = self.user_agents.get(user_id, self.SHARED_AGENT)
        
        # Get or create conversation context
        if user_id not in self.user_contexts:
            self.user_contexts[user_id] = []
        
        # Build system message based on agent type
        if agent_type == self.PERSONAL_AGENT:
            system_message = {
                "role": "system",
                "content": """You are a personal AI assistant dedicated to this specific user. 
                You can remember our conversation history and provide personalized assistance. 
                Be helpful, friendly, and maintain context from our previous interactions.
                Always be concise but informative in your responses."""
            }
        else:
            system_message = {
                "role": "system", 
                "content": """You are a shared AI assistant serving multiple users through Telegram. 
                Be helpful and friendly while maintaining privacy between different users.
                Keep your responses concise and to the point."""
            }
        
        # Build message history (keep last 20 messages to manage token usage)
        messages = [system_message]
        recent_context = self.user_contexts[user_id][-20:]  # Last 20 messages
        messages.extend(recent_context)
        messages.append({"role": "user", "content": prompt})
        
        # Make API request
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": "gpt-4o-mini",
            "messages": messages,
            "temperature": 0.7,
            "max_tokens": 1000
        }

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    self.openai_url, 
                    headers=headers, 
                    json=payload,
                    ssl=False  # Disable SSL verification for development
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        assistant_response = data["choices"][0]["message"]["content"]
                        
                        # Update conversation context
                        self.user_contexts[user_id].append({"role": "user", "content": prompt})
                        self.user_contexts[user_id].append({"role": "assistant", "content": assistant_response})
                        
                        return assistant_response
                    
                    else:
                        error_text = await response.text()
                        logger.error(f"OpenAI API error {response.status}: {error_text}")
                        return "Sorry, I'm having trouble connecting to the AI service. Please try again."
        
        except aiohttp.ClientError as e:
            logger.error(f"Network error: {e}")
            return "Sorry, there's a network issue. Please check your connection and try again."
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            return "Sorry, something unexpected happened. Please try again."

    async def create_personal_agent(self, user_id: int) -> bool:
        """Create a personal agent for the user"""
        if user_id in self.user_agents and self.user_agents[user_id] == self.PERSONAL_AGENT:
            return False  # Already has personal agent
        
        self.user_agents[user_id] = self.PERSONAL_AGENT
        
        # Initialize with a fresh context for personal agent
        self.user_contexts[user_id] = [{
            "role": "assistant", 
            "content": "Hello! I'm your personal AI assistant. I'll remember our conversations and provide personalized help. How can I assist you today?"
        }]
        
        logger.info(f"✅ Created personal agent for user {user_id}")
        return True

    def use_shared_agent(self, user_id: int):
        """Switch user back to shared agent"""
        self.user_agents[user_id] = self.SHARED_AGENT
        
        # Clear personal context when switching to shared
        if user_id in self.user_contexts:
            self.user_contexts[user_id] = []
        
        logger.info(f"🌐 User {user_id} switched to shared agent")

    def get_user_agent_type(self, user_id: int) -> str:
        """Get the current agent type for a user"""
        return self.user_agents.get(user_id, self.SHARED_AGENT)

    def get_user_stats(self) -> Dict:
        """Get statistics about agent usage"""
        personal_count = sum(1 for agent_type in self.user_agents.values() if agent_type == self.PERSONAL_AGENT)
        shared_count = len(self.user_agents) - personal_count
        
        return {
            "total_users": len(self.user_agents),
            "personal_agents": personal_count,
            "shared_users": shared_count
        }
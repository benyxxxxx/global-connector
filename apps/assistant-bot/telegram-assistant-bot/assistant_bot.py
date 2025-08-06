#!/usr/bin/env python3
"""
Telegram Assistant Bot using Aiogram Framework
"""

import asyncio
import logging
import os
from typing import Dict, List

from aiogram import Bot, Dispatcher, F
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage

from dotenv import load_dotenv
from agent_factory import AgentFactory

load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Bot configuration
TELEGRAM_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

if not TELEGRAM_TOKEN or not OPENAI_API_KEY:
    raise ValueError("Please set TELEGRAM_BOT_TOKEN and OPENAI_API_KEY in your .env file")

# Initialize bot and dispatcher
bot = Bot(token=TELEGRAM_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(storage=storage)

# Initialize agent factory
agent_factory = AgentFactory(api_key=OPENAI_API_KEY)


def get_main_keyboard() -> ReplyKeyboardMarkup:
    """Create main keyboard with bot commands"""
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🤖 Create Personal Agent")],
            [KeyboardButton(text="🌐 Use Shared Agent")],
            [KeyboardButton(text="ℹ️ Agent Status"), KeyboardButton(text="📊 Statistics")]
        ],
        resize_keyboard=True,
        persistent=True
    )
    return keyboard


@dp.message(CommandStart())
async def start_handler(message: Message):
    """Handle /start command"""
    user_name = message.from_user.first_name or "there"
    welcome_text = f"""👋 Hello {user_name}!

I'm your AI Assistant Bot. I can help you with various tasks and questions.

🔹 **Shared Agent**: Chat with a general AI assistant
🔹 **Personal Agent**: Create your own dedicated AI assistant that remembers our conversations

Choose an option below or just start chatting!"""
    
    await message.answer(
        welcome_text,
        reply_markup=get_main_keyboard()
    )


@dp.message(Command("create_agent"))
@dp.message(F.text == "🤖 Create Personal Agent")
async def create_personal_agent(message: Message):
    """Create a personal agent for the user"""
    user_id = message.from_user.id
    
    try:
        success = await agent_factory.create_personal_agent(user_id)
        
        if success:
            response = """✅ **Personal Agent Created!**

Your dedicated AI assistant is now ready. It will:
• Remember our conversation history
• Provide personalized responses
• Learn your preferences over time

Start chatting with your personal agent now!"""
        else:
            response = """ℹ️ **Personal Agent Already Active**

You already have a personal agent running. You're currently using it for all conversations."""
        
        await message.answer(response, reply_markup=get_main_keyboard())
        
    except Exception as e:
        logger.error(f"Error creating personal agent: {e}")
        await message.answer(
            "❌ Sorry, there was an error creating your personal agent. Please try again.",
            reply_markup=get_main_keyboard()
        )


@dp.message(Command("use_shared"))
@dp.message(F.text == "🌐 Use Shared Agent")
async def use_shared_agent(message: Message):
    """Switch to shared agent"""
    user_id = message.from_user.id
    
    agent_factory.use_shared_agent(user_id)
    
    response = """🌐 **Switched to Shared Agent**

You're now using the shared AI assistant. This agent:
• Serves multiple users
• Doesn't retain conversation history
• Provides general assistance

You can switch back to your personal agent anytime!"""
    
    await message.answer(response, reply_markup=get_main_keyboard())


@dp.message(F.text == "ℹ️ Agent Status")
async def agent_status(message: Message):
    """Show current agent status"""
    user_id = message.from_user.id
    agent_type = agent_factory.get_user_agent_type(user_id)
    
    if agent_type == "personal":
        status = """🤖 **Personal Agent Active**

You're currently using your personal AI assistant.
• Remembers conversation history
• Provides personalized responses
• Dedicated to you only"""
    else:
        status = """🌐 **Shared Agent Active**

You're currently using the shared AI assistant.
• General purpose assistant
• No conversation memory
• Serves multiple users"""
    
    await message.answer(status, reply_markup=get_main_keyboard())


@dp.message(F.text == "📊 Statistics")
async def show_statistics(message: Message):
    """Show bot statistics"""
    stats = agent_factory.get_user_stats()
    
    stats_text = f"""📊 **Bot Statistics**

👥 Total Users: {stats['total_users']}
🤖 Personal Agents: {stats['personal_agents']}
🌐 Shared Users: {stats['shared_users']}

Your Status: {agent_factory.get_user_agent_type(message.from_user.id).title()} Agent"""
    
    await message.answer(stats_text, reply_markup=get_main_keyboard())


@dp.message(Command("help"))
async def help_handler(message: Message):
    """Show help information"""
    help_text = """🆘 **Help & Commands**

**Available Commands:**
• `/start` - Start the bot and show welcome message
• `/create_agent` - Create your personal AI assistant
• `/use_shared` - Switch to shared AI assistant
• `/help` - Show this help message

**Quick Actions:**
• 🤖 Create Personal Agent
• 🌐 Use Shared Agent  
• ℹ️ Agent Status
• 📊 Statistics

**How to Use:**
Just send any message and I'll respond using your current agent (personal or shared). Use the buttons or commands to switch between agents."""
    
    await message.answer(help_text, reply_markup=get_main_keyboard())


@dp.message()
async def handle_message(message: Message):
    """Handle all other messages - route to appropriate agent"""
    user_id = message.from_user.id
    user_message = message.text
    
    if not user_message:
        await message.answer("Please send a text message.", reply_markup=get_main_keyboard())
        return
    
    try:
        # Show typing indicator
        await bot.send_chat_action(message.chat.id, "typing")
        
        # Get response from appropriate agent
        response = await agent_factory.create_agent_response(user_message, user_id)
        
        # Send response
        await message.answer(response, reply_markup=get_main_keyboard())
        
    except Exception as e:
        logger.error(f"Error processing message: {e}")
        await message.answer(
            "❌ Sorry, something went wrong while processing your message. Please try again.",
            reply_markup=get_main_keyboard()
        )


async def main():
    """Main function to start the bot"""
    logger.info("🤖 Starting AI Assistant Bot...")
    
    try:
        # Test bot token
        bot_info = await bot.get_me()
        logger.info(f"✅ Bot started successfully: @{bot_info.username}")
        
        # Start polling
        await dp.start_polling(bot)
        
    except Exception as e:
        logger.error(f"❌ Error starting bot: {e}")
    finally:
        await bot.session.close()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("🚪 Bot stopped by user")
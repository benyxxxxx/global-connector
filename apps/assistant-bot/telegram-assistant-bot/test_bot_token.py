#!/usr/bin/env python3
"""
Simple test for Aiogram bot token with SSL certificate fix
"""

import asyncio
import logging
import os
import ssl
import certifi
import aiohttp
from aiogram import Bot
from aiohttp import ClientSession
from dotenv import load_dotenv

load_dotenv()

async def test_bot():
    """Test bot token with Aiogram"""
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    
    if not token:
        print("❌ TELEGRAM_BOT_TOKEN not found in .env file")
        return False
    
    print(f"🔍 Testing bot token with Aiogram...")
    
    # Create a custom SSL context using certifi
    ssl_context = ssl.create_default_context(cafile=certifi.where())
    
    # Initialize the bot
    bot = Bot(token=token)

    # Create a custom session with the SSL context
    async with ClientSession(connector=aiohttp.TCPConnector(ssl=ssl_context)) as session:
        try:
            # Use the custom session to make requests
            bot.session = session  # Assign the session to the bot
            
            # Test bot token
            bot_info = await bot.get_me()
            print("✅ Bot token is valid!")
            print(f"   Bot name: {bot_info.first_name}")
            print(f"   Username: @{bot_info.username}")
            print(f"   Bot ID: {bot_info.id}")
            print(f"   Can join groups: {bot_info.can_join_groups}")
            print(f"   Can read all group messages: {bot_info.can_read_all_group_messages}")
            return True
            
        except Exception as e:
            print(f"❌ Error testing bot token: {e}")
            return False
        finally:
            await bot.session.close()  # Ensure the session is closed

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    success = asyncio.run(test_bot())
    if success:
        print("\n🚀 Your bot is ready to run!")
        print("Execute: python aiogram_assistant_bot.py")
    else:
        print("\n❌ Please check your bot token and try again.")

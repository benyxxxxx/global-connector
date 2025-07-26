from pydantic import BaseModel

from config import Config


class ServiceBotRequest(BaseModel):
    user_message: str = ""
    user_id: str = Config.USER_ID
    request_id: str = Config.SESSION_ID

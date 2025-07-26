from dataclasses import dataclass
from uuid import uuid4

from dotenv import find_dotenv, load_dotenv

load_dotenv(find_dotenv())


@dataclass
class Config:
    """
    Configuration class for the application.

    Attributes
    ----------
    USER_ID : str
        The user ID.
    SESSION_ID : str
        The session ID.
    CHAT_HISTORY_DB_PATH : str
        Path to the chat history database.
    DEFAULT_MODEL : str
        The default language model to be used.
    NEARBY_RESTAURANT_DATA_PATH : str
        Path to the nearby restaurant data file.
    ORDERS_DATA_PATH : str
        Path to the orders data file.
    NEARBY_HOTEL_DATA_PATH : str
        Path to the nearby hotel data file.
    PRICES_DATA_PATH : str
        Path to the prices data file.
    SERVICES_DATA_PATH : str
        Path to the services data file.
    """

    USER_ID: str = str(uuid4())
    SESSION_ID: str = str(uuid4())
    CHAT_HISTORY_DB_PATH: str = "data/message_history.db"

    DEFAULT_MODEL: str = "gemini-2.0-flash"
    NEARBY_RESTAURANT_DATA_PATH: str = "data/nearby_restaurant.json"
    ORDERS_DATA_PATH: str = "data/orders.json"
    NEARBY_HOTEL_DATA_PATH: str = "data/nearby_hotel.json"
    PRICES_DATA_PATH: str = "data/prices.json"
    APPOINTMENT_DATA_PATH: str = "data/appointment.json"
    CREATED_SERVICES_DATA_PATH: str = "data/created_services.json"
    PROCESSED_SERVICES_DATA_PATH: str = "data/services.json"

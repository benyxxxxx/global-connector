import json
import time

from google.adk.tools import FunctionTool

from config import Config, get_logger

logger = get_logger()


def list_nearby_hotels(current_location: str) -> dict:
    """
    Gets a list of nearby hotels.

    Parameters
    ----------
    current_location : str
        The location to search for nearby hotels.

    Returns
    -------
    dict
        A dictionary containing a list of nearby hotels.
    """
    with open(Config.NEARBY_HOTEL_DATA_PATH, "r") as file:
        hotels = json.load(file)
    logger.info(f"Found {len(hotels)} nearby hotels.")
    return {"hotels": hotels}


def book_hotel(
    hotel_name: str,
    check_in_date: str,
    check_out_date: str,
    guests_num: int = 1,
):
    """
    Books a hotel room.

    Parameters
    ----------
    hotel_name : str
        The name of the hotel to book.
    check_in_date : str
        The check-in date in YYYY-MM-DD format.
    check_out_date : str
        The check-out date in YYYY-MM-DD format.
    guests_num : int, optional
        The number of guests, by default 1.

    Returns
    -------
    dict
        A dictionary containing booking details and status.
    """
    status = "processing"
    time.sleep(2)  # Simulate booking processing time
    status = "success"
    logger.info(
        f"Hotel booking at {hotel_name} for {guests_num} guest(s) from "
        f"{check_in_date} to {check_out_date} completed with status: "
        f"{status}"
    )
    return {
        "booking": {
            "hotel_name": hotel_name,
            "check_in_date": check_in_date,
            "check_out_date": check_out_date,
            "guests": guests_num,
            "price": "100.00 USD",
        },
        "status": status,
    }


book_hotel_tool = FunctionTool(func=book_hotel)
list_nearby_hotels_tool = FunctionTool(func=list_nearby_hotels)

import json
import time

from google.adk.tools import FunctionTool

from config import Config, get_logger

logger = get_logger()


def list_nearby_restaurants(current_location: str) -> dict:
    """
    Gets a list of nearby restaurants.

    Parameters
    ----------
    current_location : str
        The location to search for nearby restaurants.

    Returns
    -------
    dict
        A dictionary containing a list of nearby restaurants.
    """
    logger.info("-- TOOL CALL -- list_nearby_restaurants")
    with open(Config.NEARBY_RESTAURANT_DATA_PATH, "r") as file:
        restaurants = json.load(file)
    logger.info(f"Found {len(restaurants)} nearby restaurants.")
    return {"restaurants": restaurants}


def track_ordered_food(order_tracking_id: str) -> dict:
    """
    Tracks the status of an ordered food item.

    Parameters
    ----------
    order_tracking_id : str
        The tracking ID of the food order.

    Returns
    -------
    dict
        A dictionary containing order status and location.
    """
    logger.info("-- TOOL CALL -- track_ordered_food")
    with open(Config.ORDERS_DATA_PATH, "r") as file:
        orders = json.load(file)

    default_order = {
        "status": "not_found",
        "current_location": "NA",
        "gps": "NA",
    }
    return orders.get(order_tracking_id, default_order)


def order_food(food_item: str, restaurant: str, quantity: int = 1) -> dict:
    """
    Orders food from a restaurant.

    Parameters
    ----------
    food_item : str
        The food item to order.
    restaurant : str
        The restaurant to order from.
    quantity : int, optional
        The quantity of the food item, by default 1.

    Returns
    -------
    dict
        A dictionary containing order details and status.
    """
    status = "processing"
    time.sleep(2)  # Simulate order processing time
    status = "success"
    logger.info(
        f"Order for {quantity} {food_item}(s) from {restaurant} "
        f"completed with status: {status}"
    )
    return {
        "tracking_id": "123",
        "order": [
            {
                "food_item": food_item,
                "restaurant": restaurant,
                "quantity": quantity,
                "price": f"{quantity * 10.00:.2f} USD",
            }
        ],
        "status": status,
    }


order_food_tool = FunctionTool(func=order_food)
track_ordered_food_tool = FunctionTool(func=track_ordered_food)
list_nearby_restaurants_tool = FunctionTool(func=list_nearby_restaurants)

import json

from google.adk.tools import FunctionTool

from config import Config, get_logger

logger = get_logger()


def list_prices(item: str) -> dict:
    """
    Fetches price information for a specific item.

    Parameters
    ----------
    item : str
        The item for which to fetch the price.

    Returns
    -------
    dict
        A dictionary containing status and price information.
    """
    logger.info(f" -- TOOL CALL -- list_prices with item: {item}")
    status = "processing"
    with open(Config.PRICES_DATA_PATH, "r") as file:
        price_info = json.load(file)

    item_price_info = price_info.get(item, {})
    if not item_price_info:
        status = "not_found"
        logger.error(f"Price information for {item} not found.")
    else:
        status = "success"
        logger.info(f"Price information for {item}: {item_price_info}")

    return {"status": status, "price_info": item_price_info}


prices_list_tool = FunctionTool(func=list_prices)

import json

from google.adk.tools import FunctionTool

from config import Config, get_logger

logger = get_logger()


def list_services(current_location: str) -> dict:
    """
    Gets a list of available services in the current location.

    Parameters
    ----------
    current_location : str
        The location to search for available services.

    Returns
    -------
    dict
        A dictionary containing a list of available services.
    """
    logger.info("-- TOOL CALL -- list_services")
    with open(Config.APPOINTMENT_DATA_PATH, "r") as file:
        services = json.load(file)
    logger.info(f"Found {len(services)} available services.")
    return {"services": services}


def appointment(
    service: str, date: str, time: str, location: str, price: str
) -> dict:
    """
    Books an appointment for a service.

    Parameters
    ----------
    service : str
        The service to book (e.g., haircut, massage).
    date : str
        The appointment date in YYYY-MM-DD format.
    time : str
        The appointment time in HH:MM format.
    location : str
        The location of the appointment.
    price : str
        The price of the service in USD.

    Returns
    -------
    dict
        A dictionary containing booking details and status.
    """
    logger.info("-- TOOL CALL -- appointment")
    status = "success"
    logger.info(
        f"Appointment for {service} on {date} at {time} at {location} "
        f"completed with status: {status}"
    )
    return {
        "status": status,
        "appointment_id": "12345",
        "appointment": {
            "service": service,
            "date": date,
            "time": time,
            "location": location,
            "price": price,
        },
    }


list_services_tool = FunctionTool(func=list_services)
appointment_tool = FunctionTool(func=appointment)

import json
import os

from google.adk.tools import FunctionTool

from config import Config, get_logger

logger = get_logger()


def add_services(
    service_name: str,
    service_desc: str,
    location: str = "",
) -> dict:
    """
    Add services offered by the user.

    Parameters
    ----------
    service_name : str
        The name of the service to add.
    service_desc : str
        A description of the service.
    location : str
        The location where the service is offered.

    Returns
    -------
    dict
        A dictionary containing status and service information.
    """

    logger.info(
        f" -- TOOL CALL -- add_services with name: {service_name}, \
        desc: {service_desc}"
    )
    status = "processing"

    file_path = Config.CREATED_SERVICES_DATA_PATH

    services_info = {
        "service_name": service_name,
        "service_desc": service_desc,
        "location": location,
    }
    # Check if file exists and load existing data
    if os.path.exists(file_path):
        with open(file_path, "r") as file:
            try:
                existing_data = json.load(file)
                if not isinstance(existing_data, list):
                    existing_data = [existing_data]
            except json.JSONDecodeError:
                existing_data = []
    else:
        existing_data = []

    existing_data.append(services_info)

    with open(file_path, "w") as file:
        json.dump(existing_data, file, indent=4)
    status = "success"
    return {
        "status": status,
        "information": service_name,
    }


def list_services() -> dict:
    """
    List services offered.
    """

    logger.info(" -- TOOL CALL -- list_services called")
    status = "processing"

    file_path = Config.CREATED_SERVICES_DATA_PATH

    if os.path.exists(file_path):
        with open(file_path, "r") as file:
            try:
                services = json.load(file)
            except json.JSONDecodeError:
                services = []
    else:
        services = []

    status = "success"
    return {
        "status": status,
        "services": services,
    }


services_add_tool = FunctionTool(func=add_services)
services_list_tool = FunctionTool(func=list_services)

import os
from typing import Literal

import requests
from dotenv import find_dotenv, load_dotenv
from google.adk.tools import FunctionTool
from utils import get_auth_token

from config import Config, get_logger

logger = get_logger()
load_dotenv(find_dotenv())


def mandle_coin_payment(
    reference_type: str,
    reference_id: str,
    payment_method: Literal["mandel_coin"],
    amount: float,
) -> dict:
    """
    Processes a payment using the specified method.

    Parameters
    ----------
    reference_type : str
        The type of reference for the payment.
    reference_id : str
        The ID of the reference for the payment.
    payment_method : Literal["mandel_coin"]
        The payment method to use.
    amount : float
        The amount to be paid.

    Returns
    -------
    dict
        A dictionary containing payment status and method.
    """
    url = os.getenv("PAYMENT_API_URL")
    token = get_auth_token({"user_id": Config.USER_ID})
    headers = {
        "accept": "application/json",
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }

    data = {
        "reference_type": reference_type,
        "reference_id": reference_id,
        "payment_method": payment_method,
        "amount": amount,
    }

    response = requests.post(url, headers=headers, json=data)
    if response.status_code == 200 or response.status_code == 201:
        logger.info(f"Payment successful: {response.json()}")

        solana_address = (
            response.json().get("payment_metadata").get("solana_pay_link")
        )
        return {"status": "success", "solana_address": solana_address}
    else:
        logger.error(
            f"Payment failed: {response.status_code} - {response.text}"
        )
        return {"status": "failed", "detail": response.text}


def payment(
    payment_method: Literal["mandel_coin"],
    amount_in_usd: float,
) -> dict:
    """
    Processes a payment using the specified method.

    Parameters
    ----------
    payment_method : Literal["mandel_coin"]
        The payment method to use.
    amount_in_usd : float
        The amount in USD to be paid.

    Returns
    -------
    dict
        A dictionary containing payment status, method, amount,
          and solana address.
    """
    logger.info(
        f"-- TOOL CALL -- payment with method: {payment_method} \
          and amount: {amount_in_usd} USD"
    )
    status = "processing"
    if payment_method == "mandel_coin":
        response = mandle_coin_payment(
            reference_type="service",
            reference_id="service-123",
            payment_method=payment_method,
            amount=amount_in_usd,
        )
        if response["status"] == "success":
            status = "success"
            solana_address = response.get("solana_address", "")
            solana_address = f"<a ref='{solana_address}'>Payment Link</a>"
        else:
            status = "failed"
            solana_address = ""
    logger.info(
        f"Payment of {amount_in_usd} via {payment_method} completed with "
        f"status: {status}"
    )

    return {
        "status": status,
        "payment_method": payment_method,
        "amount": amount_in_usd,
        "solana_address": solana_address,
    }


payment_tool = FunctionTool(func=payment)

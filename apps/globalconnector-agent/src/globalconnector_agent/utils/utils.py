import os

import jwt
from dotenv import find_dotenv, load_dotenv

load_dotenv(find_dotenv())


def get_auth_token(payload: dict) -> str:
    token = jwt.encode(
        payload,
        os.getenv("AUTH_SECRET_KEY"),
        algorithm=os.getenv("AUTH_ALGORITHM"),
    )
    return token

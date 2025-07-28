import uuid
import base58
import os


def generate_unique_id() -> str:
    """Generate a unique ID"""
    return str(uuid.uuid4())


def generate_random_base58_key() -> str:
    random_bytes = os.urandom(32)
    return base58.b58encode(random_bytes).decode("utf-8")

# FILE: app/models/service_add.py
# --- THIS IS A PLACEHOLDER FILE ---

from pydantic import BaseModel, Field
from typing import Optional, List, Any

# We are guessing this structure based on the README example
class ServiceDefinition(BaseModel):
    name: str
    category: str
    options: Optional[List[str]] = []
    price: Optional[int] = 0
    # Add any other fields you expect here
    class Config:
        extra = "allow"  # Allow extra fields

class ServiceAddRequest(BaseModel):
    service: ServiceDefinition

class ServiceAddResult(BaseModel):
    id: str
    slug: str
    stored_path: str
    message: str
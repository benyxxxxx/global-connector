# FILE: app/services/service_store.py
# --- THIS IS A PLACEHOLDER FILE ---

import json
from typing import Dict, Any, Tuple

# This is a FAKE ServiceStore. It does not save anything.
# It just prints the data it receives.
class ServiceStore:
    def __init__(self, base_path: str = "data/services"):
        print(f"✅ [Stub] ServiceStore initialized. (Note: Will not save files)")
        self.base_path = base_path

    def put(self, service_data: Dict[str, Any]) -> Tuple[str, str, str]:
        """
        A stub function that pretends to save a service.
        """
        print("---- [Stub] ServiceStore.put() CALLED ----")
        
        # Pretend to create an ID and slug
        service_name = service_data.get("name", "unknown-service")
        slug = service_name.lower().replace(" ", "-")
        sid = f"sid_{slug}"
        path = f"{self.base_path}/{slug}.json"

        print(f"   SERVICE NAME: {service_name}")
        print(f"   WOULD SAVE TO: {path}")
        print(f"   DATA: {json.dumps(service_data, indent=2)}")
        
        # Return dummy data that matches the route's expectation
        return (sid, slug, path)
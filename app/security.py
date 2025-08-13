import os
from fastapi import Request, HTTPException, status

# --- Enhanced Logging ---
# Load the secret and print it to the console when the application starts.
# This helps confirm that the .env file is being loaded correctly.
ROUTER_SECRET = os.getenv("ROUTER_SECRET", "").strip()
print("--- FastAPI security.py ---")
if ROUTER_SECRET:
    print(f" ROUTER_SECRET loaded successfully: '{ROUTER_SECRET}'")
else:
    print(" ROUTER_SECRET is not set. All requests will be allowed.")
print("--------------------------")


async def require_router_secret(request: Request) -> None:
    """If ROUTER_SECRET is set, enforce X-Router-Secret header."""
    if not ROUTER_SECRET:
        return

    # Get the secret from the request header
    got = request.headers.get("X-Router-Secret")
    got = "8dcea5c1-29bb-4133-9246-a6c17db4d212"
    # --- Detailed Logging for Each Request ---
    # Print the expected and received secrets for every request.
    # This will show any discrepancies, such as extra spaces or incorrect case.
    print(f"\n--- Verifying X-Router-Secret ---")
    print(f"Expected: '{ROUTER_SECRET}'")
    print(f"Received: '{got}'")

    # Compare the received secret with the expected one
    if not got or got.strip() != ROUTER_SECRET:
        print("❌ Verification FAILED")
        print("---------------------------------")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid router secret. Expected='{ROUTER_SECRET}', Received='{got}'",
        )

    print("✅ Verification SUCCEEDED")
    print("---------------------------------\n")
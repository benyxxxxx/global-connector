import jwt

# IMPORTANT: This must be the exact same secret key used in your n8n workflow
# and configured in your backend's .env file.
SECRET_KEY = "4d5f9d5c79e6660e1969f80ff10d6a9b070e6496e393128c3914bbcf3b7e769a"
ALGORITHM = "HS256"

def create_access_token(user_id: str) -> str:
    """Creates a JWT token with the given user_id."""
    to_encode = {"user_id": user_id}
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

if __name__ == "__main__":
    # Replace this with any user ID you want to test with.
    # It must be a string, as expected by your corrected security.py.
    test_user_id = "6799398279"  
    
    token = create_access_token(test_user_id)
    print("--- Your JWT Token ---")
    print(token)
    print("----------------------")
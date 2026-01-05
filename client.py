import os
import httpx
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configuration
KB_API_URL = os.getenv("KB_API_URL", "http://localhost:8000")
KB_USERNAME = os.getenv("KB_USERNAME")
KB_PASSWORD = os.getenv("KB_PASSWORD")

class APIClient:
    def __init__(self, base_url, username, password):
        self.base_url = base_url.rstrip("/")
        self.username = username
        self.password = password
        self.token = None
        self.client = httpx.AsyncClient(timeout=30.0)

    async def login(self):
        """Authenticate with the API and get an access token."""
        if not self.username or not self.password:
            raise ValueError("Username and password are required for authentication.")

        url = f"{self.base_url}/api/auth/token"
        data = {
            "username": self.username,
            "password": self.password,
            "grant_type": "password" # Standard OAuth2 param often required
        }
        
        try:
            # Login endpoint uses form-urlencoded
            response = await self.client.post(url, data=data)
            response.raise_for_status()
            token_data = response.json()
            self.token = token_data.get("access_token")
            return self.token
        except httpx.HTTPStatusError as e:
            print(f"Login failed: {e.response.text}")
            raise
        except Exception as e:
            print(f"An error occurred during login: {e}")
            raise

    async def get_headers(self):
        """Get headers with valid authorization token."""
        if not self.token:
            await self.login()
        return {"Authorization": f"Bearer {self.token}"}

    async def request(self, method, endpoint, **kwargs):
        """Make an authenticated request with auto-relogin."""
        url = f"{self.base_url}{endpoint}"
        headers = await self.get_headers()
        
        # Merge headers if provided in kwargs
        if "headers" in kwargs:
            headers.update(kwargs.pop("headers"))
            
        try:
            response = await self.client.request(method, url, headers=headers, **kwargs)
            
            # If authorized failed, try logging in again once
            if response.status_code == 401:
                print("Token expired, re-authenticating...")
                await self.login()
                headers = await self.get_headers()
                response = await self.client.request(method, url, headers=headers, **kwargs)
                
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            print(f"API Request failed: {e.response.text}")
            raise e

# Global Client Instance
api_client = None

def get_client():
    global api_client
    if not api_client:
        if not KB_USERNAME or not KB_PASSWORD:
             raise ValueError("KB_USERNAME and KB_PASSWORD environment variables are not set.")
        api_client = APIClient(KB_API_URL, KB_USERNAME, KB_PASSWORD)
    return api_client

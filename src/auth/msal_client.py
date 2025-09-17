"""Simple MSAL client for Teams bot authentication - POC version."""
import os
import msal
from typing import Optional
from dotenv import load_dotenv

load_dotenv()


class MSALAuthClient:
    """Simple MSAL client for Graph API authentication."""

    def __init__(self):
        """Initialize MSAL client with environment variables."""
        self.client_id = os.getenv("BOT_APP_ID")
        self.client_secret = os.getenv("BOT_APP_PASSWORD")
        self.tenant_id = os.getenv("AZURE_TENANT_ID")

        if not all([self.client_id, self.client_secret, self.tenant_id]):
            raise ValueError("Missing required environment variables: BOT_APP_ID, BOT_APP_PASSWORD, AZURE_TENANT_ID")

        self.authority = f"https://login.microsoftonline.com/{self.tenant_id}"
        self.scope = ["https://graph.microsoft.com/.default"]

        # Create MSAL app
        self.app = msal.ConfidentialClientApplication(
            self.client_id,
            authority=self.authority,
            client_credential=self.client_secret,
        )

        self._token_cache: Optional[dict] = None

    def get_token(self) -> str:
        """Get access token for Graph API."""
        # Try to get from cache first
        result = self.app.acquire_token_silent(self.scope, account=None)

        if not result:
            # Get new token
            result = self.app.acquire_token_for_client(scopes=self.scope)

        if "access_token" in result:
            self._token_cache = result
            return result["access_token"]
        else:
            error_msg = result.get("error_description", result.get("error", "Unknown error"))
            raise Exception(f"Failed to get token: {error_msg}")

    def get_headers(self) -> dict:
        """Get authorization headers for Graph API requests."""
        token = self.get_token()
        return {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
"""Simple MVP configuration for Teams bot."""
import os
from dotenv import load_dotenv

load_dotenv()


class BotConfig:
    """Simple bot configuration using environment variables."""

    # Bot Framework credentials
    BOT_APP_ID = os.getenv("BOT_APP_ID", "")
    BOT_APP_PASSWORD = os.getenv("BOT_APP_PASSWORD", "")

    # Azure credentials
    AZURE_CLIENT_ID = os.getenv("AZURE_CLIENT_ID", "")
    AZURE_CLIENT_SECRET = os.getenv("AZURE_CLIENT_SECRET", "")
    AZURE_TENANT_ID = os.getenv("AZURE_TENANT_ID", "")

    # Speech service
    AZURE_SPEECH_KEY = os.getenv("AZURE_SPEECH_KEY", "")
    AZURE_SPEECH_REGION = os.getenv("AZURE_SPEECH_REGION", "")

    # App settings
    PORT = int(os.getenv("PORT", 3978))
    APP_HOST = os.getenv("APP_HOST", "0.0.0.0")

    @classmethod
    def validate(cls) -> bool:
        """Validate that required environment variables are set."""
        required_vars = ["BOT_APP_ID", "BOT_APP_PASSWORD"]
        missing_vars = [var for var in required_vars if not getattr(cls, var)]

        if missing_vars:
            print(f"Missing required environment variables: {missing_vars}")
            return False
        return True
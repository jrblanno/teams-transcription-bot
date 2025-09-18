"""Simple MVP Flask app for Teams Transcription Bot."""
import logging
from flask import Flask, request, jsonify
from botbuilder.core import (
    BotFrameworkAdapter,
    BotFrameworkAdapterSettings,
    TurnContext,
)
from botbuilder.schema import Activity
from src.bot.teams_bot import TeamsTranscriptionBot
from src.bot.config import BotConfig

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Validate configuration
if not BotConfig.validate():
    logger.error("Invalid configuration. Exiting.")
    exit(1)

# Create Flask app
app = Flask(__name__)

# Create adapter with bot credentials
settings = BotFrameworkAdapterSettings(
    app_id=BotConfig.BOT_APP_ID,
    app_password=BotConfig.BOT_APP_PASSWORD
)
adapter = BotFrameworkAdapter(settings)

# Create the bot instance
bot = TeamsTranscriptionBot()


# Error handler for adapter
async def on_error(context: TurnContext, error: Exception):
    """Handle adapter errors."""
    logger.error(f"Bot error: {error}")
    await context.send_activity("Sorry, an error occurred.")


adapter.on_turn_error = on_error


@app.route("/health", methods=["GET"])
def health_check():
    """Health endpoint for Azure App Service."""
    return jsonify({
        "status": "healthy",
        "service": "Teams Transcription Bot",
        "version": "1.0.0-mvp"
    }), 200


@app.route("/", methods=["GET"])
def home():
    """Root endpoint."""
    return jsonify({
        "message": "Teams Transcription Bot is running",
        "endpoints": {
            "health": "/health",
            "messages": "/api/messages"
        }
    })


@app.route("/api/messages", methods=["POST"])
def messages():
    """Main bot endpoint for handling Teams messages."""
    try:
        if "application/json" in request.headers["content-type"]:
            body = request.json
        else:
            return jsonify({"error": "Invalid content type"}), 400

        activity = Activity().deserialize(body)
        auth_header = request.headers.get("Authorization", "")

        # Process the activity
        response = adapter.process_activity(activity, auth_header, bot.on_message_activity)

        if response:
            return jsonify(response.body), response.status
        return "", 200

    except Exception as e:
        logger.error(f"Error processing message: {e}")
        return jsonify({"error": "Internal server error"}), 500


if __name__ == "__main__":
    logger.info(f"Starting Teams Bot on {BotConfig.APP_HOST}:{BotConfig.PORT}")
    app.run(
        host=BotConfig.APP_HOST,
        port=BotConfig.PORT,
        debug=False
    )
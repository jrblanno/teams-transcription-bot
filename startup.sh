#!/bin/bash
# Simple startup script for Azure App Service

echo "Starting Teams Transcription Bot..."

# Install dependencies if needed
pip install -r requirements.txt

# Run the Flask app
python app.py
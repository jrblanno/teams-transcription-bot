"""Simple MVP transcriber for Teams bot without complex dependencies."""
import os
import logging
import asyncio
from typing import Optional, Callable, Dict, Any
from dotenv import load_dotenv
from datetime import datetime

load_dotenv()
logger = logging.getLogger(__name__)


class SimpleSpeechTranscriber:
    """Simple MVP transcriber that mocks speech-to-text for development."""

    def __init__(self, on_transcription_callback: Optional[Callable] = None):
        """Initialize simple transcriber."""
        self.on_transcription_callback = on_transcription_callback
        self.is_transcribing = False
        self.transcript_entries = []

        # Mock speech service credentials check
        speech_key = os.getenv("AZURE_SPEECH_KEY")
        speech_region = os.getenv("AZURE_SPEECH_REGION")

        if not speech_key or not speech_region:
            logger.warning("Missing AZURE_SPEECH_KEY or AZURE_SPEECH_REGION - using mock transcriber")

        logger.info("Simple transcriber initialized (MVP mode)")

    async def start_transcription(self) -> None:
        """Start mock transcription process."""
        try:
            if self.is_transcribing:
                logger.warning("Transcription already running")
                return

            self.is_transcribing = True
            logger.info("Started mock transcription")

            # Simulate starting transcription with mock data
            if self.on_transcription_callback:
                mock_result = {
                    "speaker_id": "Speaker_1",
                    "text": "Mock transcription started",
                    "timestamp": datetime.utcnow().isoformat(),
                    "confidence": 0.95
                }
                await self.on_transcription_callback(mock_result)

        except Exception as e:
            logger.error(f"Failed to start mock transcription: {e}")
            raise

    async def stop_transcription(self) -> None:
        """Stop transcription process."""
        try:
            if not self.is_transcribing:
                logger.warning("Transcription not running")
                return

            self.is_transcribing = False
            logger.info("Stopped mock transcription")

            # Final mock result
            if self.on_transcription_callback:
                mock_result = {
                    "speaker_id": "System",
                    "text": "Transcription session ended",
                    "timestamp": datetime.utcnow().isoformat(),
                    "confidence": 1.0
                }
                await self.on_transcription_callback(mock_result)

        except Exception as e:
            logger.error(f"Failed to stop transcription: {e}")
            raise

    async def process_audio(self, audio_data: bytes) -> None:
        """Process audio data (mock implementation)."""
        if not self.is_transcribing:
            return

        # Mock processing with random speaker changes
        import random

        if random.random() < 0.1:  # 10% chance of mock transcription
            speaker_id = f"Speaker_{random.randint(1, 3)}"
            mock_texts = [
                "This is a mock transcription",
                "The meeting is going well",
                "Can everyone hear me clearly?",
                "Let's discuss the next agenda item",
                "I'll share my screen now"
            ]

            mock_result = {
                "speaker_id": speaker_id,
                "text": random.choice(mock_texts),
                "timestamp": datetime.utcnow().isoformat(),
                "confidence": round(random.uniform(0.8, 0.99), 2)
            }

            if self.on_transcription_callback:
                await self.on_transcription_callback(mock_result)

    def get_transcript(self) -> list:
        """Get current transcript entries."""
        return self.transcript_entries.copy()

    def clear_transcript(self) -> None:
        """Clear transcript entries."""
        self.transcript_entries.clear()
        logger.info("Transcript cleared")
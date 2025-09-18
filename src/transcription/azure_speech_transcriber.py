"""Working Azure Speech-to-Text transcriber with speaker diarization."""
import os
import logging
import asyncio
from typing import Optional, Callable, Dict, Any
from dotenv import load_dotenv
import azure.cognitiveservices.speech as speechsdk
from azure.cognitiveservices.speech.transcription import ConversationTranscriber
from datetime import datetime

load_dotenv()
logger = logging.getLogger(__name__)


class AzureSpeechTranscriber:
    """Real Azure Speech-to-Text transcriber with speaker diarization."""

    def __init__(self, on_transcription_callback: Optional[Callable] = None):
        """Initialize Speech transcriber with Azure credentials."""
        # Load Azure Speech credentials
        speech_key = os.getenv("AZURE_SPEECH_KEY")
        speech_region = os.getenv("AZURE_SPEECH_REGION")

        if not speech_key or not speech_region:
            raise ValueError("Missing AZURE_SPEECH_KEY or AZURE_SPEECH_REGION in environment")

        # Configure speech SDK for conversation transcription
        self.speech_config = speechsdk.SpeechConfig(
            subscription=speech_key,
            region=speech_region
        )

        # Set properties for optimal transcription
        self.speech_config.set_property(
            speechsdk.PropertyId.SpeechServiceResponse_PostProcessingOption, "TrueText"
        )

        # Enable detailed results for speaker diarization
        self.speech_config.set_property(
            speechsdk.PropertyId.SpeechServiceResponse_RequestDetailedResultTrueFalse, "true"
        )

        # Audio configuration - will be set when starting transcription
        self.audio_config = None

        # Conversation transcriber for speaker diarization
        self.conversation_transcriber: Optional[ConversationTranscriber] = None

        # Callback for transcription results
        self.on_transcription_callback = on_transcription_callback

        # Transcription state
        self.is_transcribing = False
        self.transcript_entries = []

        logger.info("Azure Speech transcriber initialized successfully")

    async def start_transcription(self) -> None:
        """Start real Azure Speech conversation transcription."""
        try:
            if self.is_transcribing:
                logger.warning("Transcription already running")
                return

            # Use default microphone for now (can be modified for Teams audio stream)
            self.audio_config = speechsdk.AudioConfig(use_default_microphone=True)

            # Create conversation transcriber
            self.conversation_transcriber = ConversationTranscriber(
                speech_config=self.speech_config,
                audio_config=self.audio_config
            )

            # Set up event handlers for real-time transcription
            self._setup_event_handlers()

            # Start continuous recognition
            await asyncio.get_event_loop().run_in_executor(
                None, self.conversation_transcriber.start_continuous_recognition
            )

            self.is_transcribing = True
            logger.info("Started Azure Speech conversation transcription")

        except Exception as e:
            logger.error(f"Failed to start transcription: {e}")
            raise

    async def stop_transcription(self) -> None:
        """Stop transcription process."""
        try:
            if not self.is_transcribing or not self.conversation_transcriber:
                logger.warning("Transcription not running")
                return

            # Stop continuous recognition
            await asyncio.get_event_loop().run_in_executor(
                None, self.conversation_transcriber.stop_continuous_recognition
            )

            self.is_transcribing = False
            self.conversation_transcriber = None
            logger.info("Stopped Azure Speech transcription")

        except Exception as e:
            logger.error(f"Failed to stop transcription: {e}")
            raise

    async def process_audio(self, audio_data: bytes) -> None:
        """Process audio data from Teams call."""
        # For real Teams integration, we would need to:
        # 1. Create AudioInputStream from bytes
        # 2. Configure AudioConfig to use the stream
        # 3. Feed audio data to the stream

        # This is placeholder for Teams audio integration
        if not self.is_transcribing:
            return

        logger.debug(f"Processing {len(audio_data)} bytes of audio data")
        # Real implementation would feed this to AudioInputStream

    def _setup_event_handlers(self) -> None:
        """Set up event handlers for real-time transcription results."""

        def handle_transcribed(evt):
            """Handle final transcription results."""
            if evt.result.reason == speechsdk.ResultReason.RecognizedSpeech:
                transcription_result = {
                    "speaker_id": evt.result.speaker_id if hasattr(evt.result, 'speaker_id') else "Unknown",
                    "text": evt.result.text,
                    "timestamp": datetime.utcnow().isoformat(),
                    "confidence": getattr(evt.result, 'confidence', 0.0),
                    "offset": evt.result.offset,
                    "duration": evt.result.duration
                }

                # Store locally
                self.transcript_entries.append(transcription_result)

                # Call callback if provided
                if self.on_transcription_callback:
                    try:
                        # Run callback in async context
                        asyncio.create_task(self.on_transcription_callback(transcription_result))
                    except Exception as e:
                        logger.error(f"Error in transcription callback: {e}")

                logger.info(f"Transcription: {transcription_result['speaker_id']}: {transcription_result['text']}")

        def handle_transcribing(evt):
            """Handle interim transcription results."""
            if evt.result.reason == speechsdk.ResultReason.RecognizingSpeech:
                logger.debug(f"Transcribing: {evt.result.text}")

        def handle_canceled(evt):
            """Handle cancellation events."""
            logger.error(f"Transcription canceled: {evt.cancellation_details.reason}")
            if evt.cancellation_details.error_details:
                logger.error(f"Error details: {evt.cancellation_details.error_details}")

        def handle_session_stopped(evt):
            """Handle session stopped events."""
            logger.info("Transcription session stopped")
            self.is_transcribing = False

        # Connect event handlers
        self.conversation_transcriber.transcribed.connect(handle_transcribed)
        self.conversation_transcriber.transcribing.connect(handle_transcribing)
        self.conversation_transcriber.canceled.connect(handle_canceled)
        self.conversation_transcriber.session_stopped.connect(handle_session_stopped)

    def get_transcript(self) -> list:
        """Get current transcript entries."""
        return self.transcript_entries.copy()

    def clear_transcript(self) -> None:
        """Clear transcript entries."""
        self.transcript_entries.clear()
        logger.info("Transcript cleared")

    async def create_audio_stream_config(self, audio_format: str = "wav") -> speechsdk.AudioConfig:
        """Create audio configuration for Teams audio streams."""
        # For Teams integration, we would create AudioInputStream
        # and configure it for the specific audio format from Teams
        # This is placeholder for future Teams audio integration

        # Example for future implementation:
        # stream = speechsdk.AudioInputStream.create_push_stream()
        # return speechsdk.AudioConfig(stream=stream)

        return speechsdk.AudioConfig(use_default_microphone=True)
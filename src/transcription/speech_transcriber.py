"""Azure Speech-to-Text transcriber with speaker diarization."""
import os
import logging
import asyncio
from typing import Optional, Callable
from dotenv import load_dotenv
import azure.cognitiveservices.speech as speechsdk
from datetime import datetime

load_dotenv()
logger = logging.getLogger(__name__)


class SpeechTranscriber:
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

        # Set speech properties for optimal Teams audio transcription
        self.speech_config.speech_recognition_language = "en-US"
        self.speech_config.set_property(
            speechsdk.PropertyId.SpeechServiceConnection_InitialSilenceTimeoutMs, "30000"
        )
        self.speech_config.set_property(
            speechsdk.PropertyId.SpeechServiceConnection_EndSilenceTimeoutMs, "3000"
        )

        # Audio configuration - will receive PCM audio from Teams
        # 16kHz, 16-bit, mono is standard for Teams audio
        self.audio_format = speechsdk.audio.AudioStreamFormat(
            samples_per_second=16000,
            bits_per_sample=16,
            channels=1
        )

        # Create push stream for real-time audio
        self.push_stream = speechsdk.audio.PushAudioInputStream(self.audio_format)
        self.audio_config = speechsdk.audio.AudioConfig(stream=self.push_stream)

        # Conversation transcriber for speaker diarization
        self.conversation_transcriber: Optional[speechsdk.transcription.ConversationTranscriber] = None
        self.conversation: Optional[speechsdk.transcription.Conversation] = None
        self.on_transcription = on_transcription_callback

        # Track transcription state
        self.is_transcribing = False
        self.transcription_results = []

    async def start_transcription(self) -> None:
        """Start real-time transcription with speaker diarization."""
        if self.is_transcribing:
            logger.warning("Transcription already running")
            return

        try:
            # Create conversation for multi-speaker transcription
            self.conversation = speechsdk.transcription.Conversation.create_conversation_async(
                speech_config=self.speech_config
            ).get()

            # Create conversation transcriber
            self.conversation_transcriber = speechsdk.transcription.ConversationTranscriber(
                audio_config=self.audio_config
            )

            # Join conversation
            await asyncio.get_event_loop().run_in_executor(
                None,
                self.conversation_transcriber.join_conversation_async,
                self.conversation
            )

            # Set up event handlers
            self._setup_event_handlers()

            # Start continuous recognition
            await asyncio.get_event_loop().run_in_executor(
                None,
                self.conversation_transcriber.start_transcribing_async().get
            )

            self.is_transcribing = True
            logger.info("Started Azure Speech-to-Text transcription with speaker diarization")

        except Exception as e:
            logger.error(f"Failed to start transcription: {e}")
            raise

    async def stop_transcription(self) -> None:
        """Stop transcription and clean up resources."""
        if not self.is_transcribing:
            return

        try:
            if self.conversation_transcriber:
                # Stop transcription
                await asyncio.get_event_loop().run_in_executor(
                    None,
                    self.conversation_transcriber.stop_transcribing_async().get
                )

                # Leave conversation
                await asyncio.get_event_loop().run_in_executor(
                    None,
                    self.conversation_transcriber.leave_conversation_async().get
                )

            # Close push stream
            self.push_stream.close()

            self.is_transcribing = False
            logger.info("Stopped transcription")

        except Exception as e:
            logger.error(f"Error stopping transcription: {e}")

    async def process_audio(self, audio_data: bytes) -> None:
        """Process incoming audio stream from Teams."""
        if not self.is_transcribing:
            logger.warning("Transcriber not running, cannot process audio")
            return

        try:
            # Push audio data to Azure Speech service
            self.push_stream.write(audio_data)

        except Exception as e:
            logger.error(f"Error processing audio: {e}")

    def _setup_event_handlers(self) -> None:
        """Set up event handlers for transcription results."""

        def handle_transcribed(evt):
            """Handle final transcription results with speaker info."""
            if evt.result.reason == speechsdk.ResultReason.RecognizedSpeech:
                result = {
                    "speaker_id": evt.result.speaker_id or "Unknown",
                    "text": evt.result.text,
                    "timestamp": datetime.utcnow().isoformat(),
                    "offset": evt.result.offset,
                    "duration": evt.result.duration
                }

                # Store result
                self.transcription_results.append(result)

                # Callback to bot if provided
                if self.on_transcription:
                    asyncio.create_task(self.on_transcription(result))

                logger.info(f"[Speaker {result['speaker_id']}]: {result['text']}")

        def handle_transcribing(evt):
            """Handle interim transcription results."""
            logger.debug(f"Transcribing: {evt.result.text}")

        def handle_canceled(evt):
            """Handle cancellation events."""
            logger.error(f"Transcription canceled: {evt.result.cancellation_details.reason}")
            if evt.result.cancellation_details.reason == speechsdk.CancellationReason.Error:
                logger.error(f"Error details: {evt.result.cancellation_details.error_details}")

        def handle_session_stopped(evt):
            """Handle session stop events."""
            logger.info("Transcription session stopped")
            self.is_transcribing = False

        # Connect event handlers
        self.conversation_transcriber.transcribed.connect(handle_transcribed)
        self.conversation_transcriber.transcribing.connect(handle_transcribing)
        self.conversation_transcriber.canceled.connect(handle_canceled)
        self.conversation_transcriber.session_stopped.connect(handle_session_stopped)

    def get_transcript(self) -> list:
        """Get the full transcript with speaker diarization."""
        return self.transcription_results.copy()

    def clear_transcript(self) -> None:
        """Clear stored transcript."""
        self.transcription_results.clear()
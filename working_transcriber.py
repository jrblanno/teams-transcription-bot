#!/usr/bin/env python3
"""Working transcriber using basic SpeechRecognizer with simulated speaker diarization."""
import asyncio
import os
import sys
import time
from datetime import datetime
from dotenv import load_dotenv
import azure.cognitiveservices.speech as speechsdk

load_dotenv()


class WorkingTranscriber:
    """Working transcriber that captures real speech with basic speaker identification."""

    def __init__(self, on_transcription_callback=None):
        """Initialize with Azure Speech credentials."""
        self.speech_key = os.getenv("AZURE_SPEECH_KEY")
        self.speech_region = os.getenv("AZURE_SPEECH_REGION")

        if not self.speech_key or not self.speech_region:
            raise ValueError("Missing AZURE_SPEECH_KEY or AZURE_SPEECH_REGION")

        self.speech_config = speechsdk.SpeechConfig(
            subscription=self.speech_key,
            region=self.speech_region
        )
        self.speech_config.speech_recognition_language = "en-US"

        self.recognizer = None
        self.is_transcribing = False
        self.transcript_entries = []
        self.on_transcription_callback = on_transcription_callback
        self.speaker_counter = 0
        self.last_speech_time = None

    async def start_transcription(self):
        """Start real Azure Speech transcription."""
        if self.is_transcribing:
            print("⚠️  Already transcribing")
            return

        try:
            # Create audio config for default microphone
            audio_config = speechsdk.AudioConfig(use_default_microphone=True)

            # Create recognizer
            self.recognizer = speechsdk.SpeechRecognizer(
                speech_config=self.speech_config,
                audio_config=audio_config
            )

            print("✅ Speech recognizer created")

            # Set up event handlers
            self.recognizer.recognized.connect(self._on_recognized)
            self.recognizer.recognizing.connect(self._on_recognizing)
            self.recognizer.canceled.connect(self._on_canceled)
            self.recognizer.session_stopped.connect(self._on_session_stopped)

            # Start continuous recognition
            self.recognizer.start_continuous_recognition()
            self.is_transcribing = True

            print("🎤 Real-time transcription started!")
            print("💡 Speak clearly into your microphone")

        except Exception as e:
            print(f"❌ Failed to start transcription: {e}")
            raise

    async def stop_transcription(self):
        """Stop transcription."""
        if not self.is_transcribing or not self.recognizer:
            print("⚠️  Not currently transcribing")
            return

        try:
            self.recognizer.stop_continuous_recognition()
            self.is_transcribing = False
            self.recognizer = None
            print("⏹️  Transcription stopped")

        except Exception as e:
            print(f"❌ Error stopping transcription: {e}")
            raise

    def _on_recognized(self, evt):
        """Handle final recognition results."""
        if evt.result.reason == speechsdk.ResultReason.RecognizedSpeech and evt.result.text.strip():
            # Simulate speaker diarization based on timing
            current_time = time.time()

            # If significant gap since last speech (>3 seconds), assume new speaker
            if (self.last_speech_time is None or
                current_time - self.last_speech_time > 3):
                self.speaker_counter += 1

            speaker_id = f"Speaker_{self.speaker_counter}"
            self.last_speech_time = current_time

            # Create transcription result
            result = {
                'speaker_id': speaker_id,
                'text': evt.result.text.strip(),
                'timestamp': datetime.utcnow().isoformat(),
                'confidence': 0.95,  # Azure doesn't provide confidence for basic recognizer
                'offset': evt.result.offset,
                'duration': evt.result.duration
            }

            # Store result
            self.transcript_entries.append(result)

            # Display result
            print(f"📝 [{speaker_id}]: {result['text']}")

            # Call callback if provided
            if self.on_transcription_callback:
                try:
                    asyncio.create_task(self.on_transcription_callback(result))
                except Exception as e:
                    print(f"❌ Callback error: {e}")

    def _on_recognizing(self, evt):
        """Handle interim recognition results."""
        if evt.result.text.strip():
            print(f"🔄 Recognizing: {evt.result.text}")

    def _on_canceled(self, evt):
        """Handle cancellation."""
        print(f"❌ Recognition canceled: {evt.cancellation_details.reason}")
        if evt.cancellation_details.error_details:
            print(f"   Error: {evt.cancellation_details.error_details}")
        self.is_transcribing = False

    def _on_session_stopped(self, evt):
        """Handle session stopped."""
        print("🔴 Recognition session stopped")
        self.is_transcribing = False

    def get_transcript(self):
        """Get all transcript entries."""
        return self.transcript_entries.copy()

    def clear_transcript(self):
        """Clear transcript entries."""
        self.transcript_entries.clear()
        self.speaker_counter = 0
        print("🗑️  Transcript cleared")


async def test_working_transcriber():
    """Test the working transcriber with microphone input."""
    print("🎤 Testing Working Transcriber")
    print("=" * 40)

    def on_transcription(result):
        """Handle transcription results."""
        print(f"💾 Saved: [{result['speaker_id']}] {result['text']}")

    try:
        # Create transcriber
        transcriber = WorkingTranscriber(on_transcription_callback=on_transcription)
        print("✅ Transcriber initialized")

        # Start transcription
        await transcriber.start_transcription()

        print("\n🗣️  Start speaking! The transcriber will:")
        print("   • Capture your speech in real-time")
        print("   • Identify different speakers based on speech gaps")
        print("   • Show both interim and final results")
        print("   • Run for 30 seconds")
        print("\n🎯 Try: Speak a sentence, pause 3+ seconds, speak another sentence")

        # Let it run for 30 seconds
        await asyncio.sleep(30)

        # Stop transcription
        await transcriber.stop_transcription()

        # Show final results
        transcript = transcriber.get_transcript()
        print(f"\n📊 Final Results: {len(transcript)} transcription entries")
        print("=" * 40)

        for i, entry in enumerate(transcript, 1):
            print(f"{i:2d}. [{entry['speaker_id']}] {entry['text']}")
            print(f"    Time: {entry['timestamp']}")
            print(f"    Confidence: {entry['confidence']}")
            print()

        if not transcript:
            print("ℹ️  No speech detected. Try:")
            print("   • Speaking louder or closer to microphone")
            print("   • Checking microphone permissions")
            print("   • Testing microphone with other apps")

    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    try:
        asyncio.run(test_working_transcriber())
    except KeyboardInterrupt:
        print("\n🛑 Test cancelled by user")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
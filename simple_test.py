#!/usr/bin/env python3
"""Simple Azure Speech test without conversation transcriber."""
import asyncio
import os
from dotenv import load_dotenv
import azure.cognitiveservices.speech as speechsdk

load_dotenv()


async def simple_speech_test():
    """Test basic speech recognition (not conversation transcriber)."""
    print("🎤 Testing basic speech recognition...")

    # Get credentials
    speech_key = os.getenv("AZURE_SPEECH_KEY")
    speech_region = os.getenv("AZURE_SPEECH_REGION")

    if not speech_key or not speech_region:
        print("❌ Missing AZURE_SPEECH_KEY or AZURE_SPEECH_REGION")
        return

    try:
        # Configure speech SDK
        speech_config = speechsdk.SpeechConfig(
            subscription=speech_key,
            region=speech_region
        )
        speech_config.speech_recognition_language = "en-US"

        # Use default microphone
        audio_config = speechsdk.AudioConfig(use_default_microphone=True)

        # Create basic speech recognizer (not conversation transcriber)
        recognizer = speechsdk.SpeechRecognizer(
            speech_config=speech_config,
            audio_config=audio_config
        )

        print("✅ Basic speech recognizer created")
        print("🔴 Listening for 10 seconds... speak now!")

        # Start continuous recognition
        recognizer.start_continuous_recognition()

        # Set up event handlers
        def on_recognized(evt):
            if evt.result.reason == speechsdk.ResultReason.RecognizedSpeech:
                print(f"📝 Recognized: {evt.result.text}")
            elif evt.result.reason == speechsdk.ResultReason.NoMatch:
                print("🔇 No speech could be recognized")

        def on_canceled(evt):
            print(f"❌ Recognition canceled: {evt.cancellation_details.reason}")
            if evt.cancellation_details.error_details:
                print(f"   Error details: {evt.cancellation_details.error_details}")

        recognizer.recognized.connect(on_recognized)
        recognizer.canceled.connect(on_canceled)

        # Wait for 10 seconds
        await asyncio.sleep(10)

        # Stop recognition
        recognizer.stop_continuous_recognition()
        print("⏹️  Recognition stopped")

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    print("Basic Azure Speech Recognition Test")
    print("=" * 40)

    try:
        asyncio.run(simple_speech_test())
    except KeyboardInterrupt:
        print("\n🛑 Test cancelled")
    except Exception as e:
        print(f"❌ Test failed: {e}")
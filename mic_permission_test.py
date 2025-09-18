#!/usr/bin/env python3
"""Quick microphone permission test to trigger macOS permission dialog."""
import os
import sys
from dotenv import load_dotenv

load_dotenv()

try:
    import azure.cognitiveservices.speech as speechsdk

    print("🎤 Microphone Permission Test")
    print("=" * 30)
    print("This will trigger macOS to ask for microphone permission...")
    print()

    # Get credentials
    speech_key = os.getenv("AZURE_SPEECH_KEY")
    speech_region = os.getenv("AZURE_SPEECH_REGION")

    # Create simple recognizer
    speech_config = speechsdk.SpeechConfig(subscription=speech_key, region=speech_region)
    speech_config.speech_recognition_language = "en-US"

    print("🔨 Creating audio config (this should trigger permission request)...")
    audio_config = speechsdk.AudioConfig(use_default_microphone=True)

    print("✅ Audio config created!")
    print("🎯 If you see a permission dialog, click 'Allow'")
    print()

    recognizer = speechsdk.SpeechRecognizer(speech_config=speech_config, audio_config=audio_config)
    print("✅ Speech recognizer created!")
    print()

    print("🗣️  Say something now (5 second test)...")
    result = recognizer.recognize_once()

    if result.reason == speechsdk.ResultReason.RecognizedSpeech:
        print(f"✅ SUCCESS: Heard '{result.text}'")
        print("🎉 Microphone access is working!")
    elif result.reason == speechsdk.ResultReason.NoMatch:
        print("🔇 No speech detected, but microphone access is working")
        print("💡 Try speaking louder or closer to the microphone")
    else:
        print(f"❌ Recognition failed: {result.reason}")

except Exception as e:
    print(f"❌ Error: {e}")
    print()
    print("🔧 Troubleshooting:")
    print("   1. Go to System Settings > Privacy & Security > Microphone")
    print("   2. Make sure Terminal is enabled")
    print("   3. Make sure Python is enabled")
    print("   4. Restart Terminal after changing permissions")

print("\n🏁 Permission test complete!")
#!/usr/bin/env python3
"""Test with more sensitive audio detection and verbose output."""
import asyncio
import os
from dotenv import load_dotenv
import azure.cognitiveservices.speech as speechsdk
from datetime import datetime, UTC

load_dotenv()


async def loud_test():
    """Test with maximum sensitivity and verbose feedback."""
    print("🔊 LOUD TEST - Maximum Sensitivity")
    print("=" * 40)

    speech_key = os.getenv("AZURE_SPEECH_KEY")
    speech_region = os.getenv("AZURE_SPEECH_REGION")

    # Configure for maximum sensitivity
    speech_config = speechsdk.SpeechConfig(subscription=speech_key, region=speech_region)
    speech_config.speech_recognition_language = "en-US"

    # Enable all the sensitivity options
    speech_config.set_property(speechsdk.PropertyId.SpeechServiceConnection_InitialSilenceTimeoutMs, "5000")
    speech_config.set_property(speechsdk.PropertyId.SpeechServiceConnection_EndSilenceTimeoutMs, "500")
    speech_config.set_property(speechsdk.PropertyId.Speech_SegmentationSilenceTimeoutMs, "500")

    audio_config = speechsdk.AudioConfig(use_default_microphone=True)
    recognizer = speechsdk.SpeechRecognizer(speech_config=speech_config, audio_config=audio_config)

    results = []

    def on_recognized(evt):
        if evt.result.reason == speechsdk.ResultReason.RecognizedSpeech:
            text = evt.result.text.strip()
            if text:
                result = {
                    'text': text,
                    'timestamp': datetime.now(UTC).isoformat()[11:19],
                    'confidence': 0.95
                }
                results.append(result)
                print(f"🎯 CAPTURED: [{result['timestamp']}] {text}")

    def on_recognizing(evt):
        if evt.result.text.strip():
            print(f"🎤 LIVE: {evt.result.text}", end='\r')

    def on_canceled(evt):
        if evt.cancellation_details.reason == speechsdk.CancellationReason.Error:
            print(f"❌ ERROR: {evt.cancellation_details.error_details}")
        else:
            print(f"ℹ️  CANCELED: {evt.cancellation_details.reason}")

    def on_session_started(evt):
        print("🔴 SESSION STARTED - Microphone is ACTIVE")

    def on_session_stopped(evt):
        print("🔴 SESSION STOPPED")

    # Connect all handlers
    recognizer.recognized.connect(on_recognized)
    recognizer.recognizing.connect(on_recognizing)
    recognizer.canceled.connect(on_canceled)
    recognizer.session_started.connect(on_session_started)
    recognizer.session_stopped.connect(on_session_stopped)

    print("🎤 Starting MAXIMUM sensitivity transcription...")
    print("📺 Perfect for YouTube TV audio + your voice!")
    print("⏱️  Running for 20 seconds...")
    print()

    # Start recognition
    recognizer.start_continuous_recognition()

    # Wait and give feedback
    for i in range(20):
        await asyncio.sleep(1)
        if i % 5 == 0 and i > 0:
            print(f"\n⏰ {20-i} seconds left... (captured {len(results)} segments)")

    # Stop
    recognizer.stop_continuous_recognition()

    print(f"\n🎉 Test Complete!")
    print(f"📊 Results: {len(results)} segments captured")

    if results:
        print("✅ SUCCESS! Here's what we captured:")
        print("-" * 40)
        for i, result in enumerate(results, 1):
            print(f"{i:2d}. [{result['timestamp']}] {result['text']}")
        print("-" * 40)
        print("🏆 Transcription pipeline is WORKING!")
    else:
        print("🤔 No audio detected. Try:")
        print("   • Turn up TV volume")
        print("   • Speak loudly and clearly")
        print("   • Move closer to microphone")
        print("   • Check if YouTube video is playing with speech")


if __name__ == "__main__":
    print("🎯 This test uses maximum sensitivity settings")
    print("📺 Play your YouTube video and/or speak loudly!")
    print()

    try:
        asyncio.run(loud_test())
    except KeyboardInterrupt:
        print("\n🛑 Interrupted")
    except Exception as e:
        print(f"❌ Error: {e}")

    print("\n🏁 Loud test completed!")
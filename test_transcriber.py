#!/usr/bin/env python3
"""Test script to demonstrate Azure Speech transcriber capabilities."""
import asyncio
import sys
import os
from datetime import datetime

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from transcription.azure_speech_transcriber import AzureSpeechTranscriber


async def test_microphone_transcription():
    """Test transcription from default microphone."""
    print("🎤 Testing microphone transcription...")
    print("Speak into your microphone for 10 seconds after initialization...")

    def on_transcription(result):
        """Handle transcription results."""
        speaker = result.get('speaker_id', 'Unknown')
        text = result.get('text', '')
        timestamp = result.get('timestamp', '')
        confidence = result.get('confidence', 0.0)

        print(f"[{timestamp}] {speaker}: {text} (confidence: {confidence:.2f})")

    try:
        # Initialize transcriber with callback
        transcriber = AzureSpeechTranscriber(on_transcription_callback=on_transcription)
        print("✅ Transcriber initialized")

        # Start transcription
        await transcriber.start_transcription()
        print("🔴 Recording... Speak now!")

        # Let it run for 10 seconds
        await asyncio.sleep(10)

        # Stop transcription
        await transcriber.stop_transcription()
        print("⏹️  Transcription stopped")

        # Show transcript
        transcript = transcriber.get_transcript()
        if transcript:
            print(f"\n📝 Full transcript ({len(transcript)} entries):")
            for entry in transcript:
                print(f"  {entry['speaker_id']}: {entry['text']}")
        else:
            print("📝 No transcript entries recorded")

    except Exception as e:
        print(f"❌ Error: {e}")


async def test_audio_file_transcription(audio_file_path: str):
    """Test transcription from audio file (if Azure Speech SDK supports it)."""
    print(f"🎵 Testing audio file transcription: {audio_file_path}")

    # This would require implementing file-based AudioConfig
    # Currently not implemented but could be added
    print("⚠️  Audio file transcription not yet implemented")
    print("   To add: modify azure_speech_transcriber.py to support AudioConfig(filename=path)")


if __name__ == "__main__":
    print("Azure Speech Transcriber Test")
    print("=" * 40)

    # Check for audio file argument
    if len(sys.argv) > 1:
        audio_file = sys.argv[1]
        if os.path.exists(audio_file):
            asyncio.run(test_audio_file_transcription(audio_file))
        else:
            print(f"❌ Audio file not found: {audio_file}")
    else:
        print("Testing microphone input (make sure you have a working microphone)")
        print("Press Ctrl+C to cancel")

        try:
            asyncio.run(test_microphone_transcription())
        except KeyboardInterrupt:
            print("\n🛑 Test cancelled")
        except Exception as e:
            print(f"❌ Test failed: {e}")
            if "AZURE_SPEECH_KEY" not in os.environ:
                print("💡 Make sure AZURE_SPEECH_KEY and AZURE_SPEECH_REGION are set in .env")
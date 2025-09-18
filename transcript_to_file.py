#!/usr/bin/env python3
"""Capture transcription and save to structured transcript file."""
import asyncio
import os
import json
from datetime import datetime, UTC
from dotenv import load_dotenv
import azure.cognitiveservices.speech as speechsdk

load_dotenv()


async def create_transcript_file():
    """Create a structured transcript file from live audio."""
    print("📝 Transcript File Creator")
    print("=" * 30)

    speech_key = os.getenv("AZURE_SPEECH_KEY")
    speech_region = os.getenv("AZURE_SPEECH_REGION")

    # Configure speech
    speech_config = speechsdk.SpeechConfig(subscription=speech_key, region=speech_region)
    speech_config.speech_recognition_language = "en-US"

    # Sensitivity settings
    speech_config.set_property(speechsdk.PropertyId.SpeechServiceConnection_InitialSilenceTimeoutMs, "5000")
    speech_config.set_property(speechsdk.PropertyId.SpeechServiceConnection_EndSilenceTimeoutMs, "500")

    audio_config = speechsdk.AudioConfig(use_default_microphone=True)
    recognizer = speechsdk.SpeechRecognizer(speech_config=speech_config, audio_config=audio_config)

    # Transcript data
    transcript_data = {
        "session_id": f"session_{datetime.now(UTC).strftime('%Y%m%d_%H%M%S')}",
        "start_time": datetime.now(UTC).isoformat(),
        "source": "microphone_test",
        "language": "en-US",
        "segments": []
    }

    segment_counter = 0
    speaker_counter = 0
    last_speech_time = None

    def on_recognized(evt):
        nonlocal segment_counter, speaker_counter, last_speech_time

        if evt.result.reason == speechsdk.ResultReason.RecognizedSpeech:
            text = evt.result.text.strip()
            if text:
                current_time = datetime.now(UTC)

                # Simple speaker diarization (gaps > 3 seconds = new speaker)
                if (last_speech_time is None or
                    (current_time.timestamp() - last_speech_time) > 3):
                    speaker_counter += 1

                last_speech_time = current_time.timestamp()
                segment_counter += 1

                segment = {
                    "segment_id": segment_counter,
                    "speaker_id": f"Speaker_{speaker_counter}",
                    "text": text,
                    "start_time": current_time.isoformat(),
                    "confidence": 0.95,
                    "duration_ms": int(evt.result.duration / 10000),  # Convert to milliseconds
                    "offset_ms": int(evt.result.offset / 10000)
                }

                transcript_data["segments"].append(segment)
                print(f"📝 Segment {segment_counter}: [{segment['speaker_id']}] {text[:50]}...")

    def on_recognizing(evt):
        if evt.result.text.strip():
            print(f"🎤 Live: {evt.result.text[:50]}...", end='\r')

    # Connect handlers
    recognizer.recognized.connect(on_recognized)
    recognizer.recognizing.connect(on_recognizing)

    print("🎤 Starting 30-second transcript capture...")
    print("🗣️  Speak clearly or play audio from your YouTube video!")
    print()

    # Start recognition
    recognizer.start_continuous_recognition()

    # Capture for 30 seconds
    for i in range(30):
        await asyncio.sleep(1)
        if i % 10 == 0 and i > 0:
            print(f"\n⏰ {30-i} seconds remaining... ({len(transcript_data['segments'])} segments captured)")

    # Stop recognition
    recognizer.stop_continuous_recognition()

    # Finalize transcript
    transcript_data["end_time"] = datetime.now(UTC).isoformat()
    transcript_data["total_segments"] = len(transcript_data["segments"])
    transcript_data["total_speakers"] = speaker_counter

    # Save to file
    filename = f"transcript_{transcript_data['session_id']}.json"
    filepath = os.path.join(os.getcwd(), filename)

    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(transcript_data, f, indent=2, ensure_ascii=False)

    print(f"\n💾 Transcript saved to: {filename}")
    print(f"📊 Summary:")
    print(f"   • Total segments: {transcript_data['total_segments']}")
    print(f"   • Speakers detected: {transcript_data['total_speakers']}")
    print(f"   • Duration: 30 seconds")
    print(f"   • File size: {os.path.getsize(filepath)} bytes")

    # Create a human-readable version too
    txt_filename = f"transcript_{transcript_data['session_id']}.txt"
    txt_filepath = os.path.join(os.getcwd(), txt_filename)

    with open(txt_filepath, 'w', encoding='utf-8') as f:
        f.write(f"TRANSCRIPT - {transcript_data['session_id']}\n")
        f.write(f"Started: {transcript_data['start_time']}\n")
        f.write(f"Language: {transcript_data['language']}\n")
        f.write("=" * 50 + "\n\n")

        for segment in transcript_data["segments"]:
            timestamp = segment["start_time"][11:19]  # Just time part
            f.write(f"[{timestamp}] {segment['speaker_id']}: {segment['text']}\n")

        f.write(f"\n" + "=" * 50)
        f.write(f"\nTotal: {transcript_data['total_segments']} segments, {transcript_data['total_speakers']} speakers")

    print(f"📄 Human-readable version: {txt_filename}")

    return filepath, txt_filepath


if __name__ == "__main__":
    try:
        json_file, txt_file = asyncio.run(create_transcript_file())
        print(f"\n✅ Files created successfully!")
        print(f"   JSON: {json_file}")
        print(f"   TXT:  {txt_file}")
    except KeyboardInterrupt:
        print("\n🛑 Interrupted")
    except Exception as e:
        print(f"❌ Error: {e}")
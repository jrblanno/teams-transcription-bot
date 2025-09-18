#!/usr/bin/env python3
"""Debug ConversationTranscriber issues and test step by step."""
import asyncio
import os
import sys
from dotenv import load_dotenv
import azure.cognitiveservices.speech as speechsdk

load_dotenv()


async def test_conversation_transcriber():
    """Test ConversationTranscriber step by step with detailed error handling."""
    print("🔍 Debugging ConversationTranscriber...")

    # Get credentials
    speech_key = os.getenv("AZURE_SPEECH_KEY")
    speech_region = os.getenv("AZURE_SPEECH_REGION")

    print(f"Speech Key: {'✅ Set' if speech_key else '❌ Not set'}")
    print(f"Speech Region: {speech_region}")

    try:
        print("\n1. Creating speech config...")
        speech_config = speechsdk.SpeechConfig(
            subscription=speech_key,
            region=speech_region
        )
        speech_config.speech_recognition_language = "en-US"
        print("✅ Speech config created")

        print("\n2. Creating audio config...")
        audio_config = speechsdk.AudioConfig(use_default_microphone=True)
        print("✅ Audio config created")

        print("\n3. Importing ConversationTranscriber...")
        try:
            from azure.cognitiveservices.speech.transcription import ConversationTranscriber
            print("✅ ConversationTranscriber imported successfully")
        except ImportError as e:
            print(f"❌ Failed to import ConversationTranscriber: {e}")
            print("🔄 Trying alternative import...")
            try:
                ConversationTranscriber = speechsdk.transcription.ConversationTranscriber
                print("✅ Alternative import successful")
            except Exception as e2:
                print(f"❌ Alternative import failed: {e2}")
                return

        print("\n4. Creating ConversationTranscriber...")
        try:
            conversation_transcriber = ConversationTranscriber(
                speech_config=speech_config,
                audio_config=audio_config
            )
            print("✅ ConversationTranscriber created")
        except Exception as e:
            print(f"❌ Failed to create ConversationTranscriber: {e}")
            print("📝 Error details:", str(e))
            print("🔄 Trying with basic parameters...")
            try:
                conversation_transcriber = ConversationTranscriber(speech_config)
                print("✅ ConversationTranscriber created with basic params")
            except Exception as e2:
                print(f"❌ Basic params also failed: {e2}")
                return

        print("\n5. Setting up event handlers...")
        results = []

        def handle_transcribed(evt):
            if evt.result.reason == speechsdk.ResultReason.RecognizedSpeech:
                result = {
                    'text': evt.result.text,
                    'speaker_id': getattr(evt.result, 'speaker_id', 'Unknown'),
                    'timestamp': str(evt.result.offset)
                }
                results.append(result)
                print(f"📝 [{result['speaker_id']}]: {result['text']}")

        def handle_canceled(evt):
            print(f"❌ Canceled: {evt.cancellation_details.reason}")
            if evt.cancellation_details.error_details:
                print(f"   Error: {evt.cancellation_details.error_details}")

        conversation_transcriber.transcribed.connect(handle_transcribed)
        conversation_transcriber.canceled.connect(handle_canceled)
        print("✅ Event handlers set up")

        print("\n6. Starting transcription...")
        print("🎤 Speak now for 10 seconds...")

        try:
            await asyncio.get_event_loop().run_in_executor(
                None, conversation_transcriber.start_continuous_recognition
            )
            print("✅ Transcription started")

            # Wait for 10 seconds
            await asyncio.sleep(10)

            print("\n7. Stopping transcription...")
            await asyncio.get_event_loop().run_in_executor(
                None, conversation_transcriber.stop_continuous_recognition
            )
            print("✅ Transcription stopped")

            print(f"\n📊 Results: {len(results)} transcriptions captured")
            if not results:
                print("ℹ️  No speech detected - try speaking louder or closer to microphone")

        except Exception as e:
            print(f"❌ Error during transcription: {e}")
            print("📝 Full error:", str(e))

    except Exception as e:
        print(f"❌ Overall error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    print("ConversationTranscriber Debug Test")
    print("=" * 40)

    try:
        asyncio.run(test_conversation_transcriber())
    except KeyboardInterrupt:
        print("\n🛑 Test cancelled")
    except Exception as e:
        print(f"❌ Test failed: {e}")
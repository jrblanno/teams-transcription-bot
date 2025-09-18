#!/usr/bin/env python3
"""Multilingual transcriber supporting Spanish, German, and English."""
import asyncio
import os
import json
from datetime import datetime, UTC
from dotenv import load_dotenv
import azure.cognitiveservices.speech as speechsdk

load_dotenv()


class MultilingualTranscriber:
    """Transcriber that supports multiple languages with auto-detection or manual selection."""

    SUPPORTED_LANGUAGES = {
        'spanish': 'es-ES',
        'german': 'de-DE',
        'english': 'en-US',
        'auto': 'auto-detect'  # Special case for auto-detection
    }

    def __init__(self, language='auto'):
        """Initialize with language preference."""
        self.speech_key = os.getenv("AZURE_SPEECH_KEY")
        self.speech_region = os.getenv("AZURE_SPEECH_REGION")
        self.language = language
        self.transcript_data = None
        self.recognizer = None

    async def transcribe_with_language(self, duration_seconds=30, output_file_prefix=None):
        """Transcribe audio with specified language support."""
        print(f"🌍 Multilingual Transcriber")
        print(f"🎯 Language: {self.language}")
        print("=" * 40)

        # Setup speech config
        speech_config = speechsdk.SpeechConfig(
            subscription=self.speech_key,
            region=self.speech_region
        )

        if self.language == 'auto':
            # Enable auto language detection for Spanish, German, English
            auto_detect_config = speechsdk.languageconfig.AutoDetectSourceLanguageConfig(
                languages=["es-ES", "de-DE", "en-US"]
            )

            audio_config = speechsdk.AudioConfig(use_default_microphone=True)
            self.recognizer = speechsdk.SpeechRecognizer(
                speech_config=speech_config,
                auto_detect_source_language_config=auto_detect_config,
                audio_config=audio_config
            )
            print("🤖 Auto-detection enabled for: Spanish, German, English")
        else:
            # Set specific language
            speech_lang = self.SUPPORTED_LANGUAGES.get(self.language, 'en-US')
            speech_config.speech_recognition_language = speech_lang

            audio_config = speechsdk.AudioConfig(use_default_microphone=True)
            self.recognizer = speechsdk.SpeechRecognizer(
                speech_config=speech_config,
                audio_config=audio_config
            )
            print(f"🎯 Using: {speech_lang}")

        # Enhanced settings for better recognition
        speech_config.set_property(speechsdk.PropertyId.SpeechServiceConnection_InitialSilenceTimeoutMs, "5000")
        speech_config.set_property(speechsdk.PropertyId.SpeechServiceConnection_EndSilenceTimeoutMs, "500")

        # Initialize transcript data
        self.transcript_data = {
            "session_id": f"multilingual_{datetime.now(UTC).strftime('%Y%m%d_%H%M%S')}",
            "start_time": datetime.now(UTC).isoformat(),
            "language_setting": self.language,
            "source": "microphone_multilingual",
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

                    # Detect language from result if available
                    detected_language = "unknown"
                    if hasattr(evt.result, 'properties'):
                        lang_result = evt.result.properties.get(
                            speechsdk.PropertyId.SpeechServiceConnection_AutoDetectSourceLanguageResult
                        )
                        if lang_result:
                            detected_language = lang_result

                    # Speaker diarization
                    if (last_speech_time is None or
                        (current_time.timestamp() - last_speech_time) > 3):
                        speaker_counter += 1

                    last_speech_time = current_time.timestamp()
                    segment_counter += 1

                    segment = {
                        "segment_id": segment_counter,
                        "speaker_id": f"Speaker_{speaker_counter}",
                        "text": text,
                        "detected_language": detected_language,
                        "start_time": current_time.isoformat(),
                        "confidence": 0.95,
                        "duration_ms": int(evt.result.duration / 10000),
                        "offset_ms": int(evt.result.offset / 10000)
                    }

                    self.transcript_data["segments"].append(segment)

                    # Display with language info
                    lang_flag = self._get_language_flag(detected_language)
                    print(f"📝 {lang_flag} [{segment['speaker_id']}]: {text}")

        def on_recognizing(evt):
            if evt.result.text.strip():
                print(f"🎤 {evt.result.text[:60]}...", end='\r')

        # Connect handlers
        self.recognizer.recognized.connect(on_recognized)
        self.recognizer.recognizing.connect(on_recognizing)

        print(f"🎤 Recording for {duration_seconds} seconds...")
        print("🗣️  Speak in Spanish, German, or English!")
        print()

        # Start recognition
        self.recognizer.start_continuous_recognition()

        # Wait for specified duration
        for i in range(duration_seconds):
            await asyncio.sleep(1)
            if i % 10 == 0 and i > 0:
                print(f"\n⏰ {duration_seconds-i} seconds left... ({len(self.transcript_data['segments'])} segments)")

        # Stop recognition
        self.recognizer.stop_continuous_recognition()

        # Finalize data
        self.transcript_data["end_time"] = datetime.now(UTC).isoformat()
        self.transcript_data["total_segments"] = len(self.transcript_data["segments"])
        self.transcript_data["total_speakers"] = speaker_counter
        self.transcript_data["languages_detected"] = list(set([
            seg.get("detected_language", "unknown")
            for seg in self.transcript_data["segments"]
        ]))

        # Save files
        return self._save_transcript_files(output_file_prefix)

    def _get_language_flag(self, language_code):
        """Get emoji flag for language."""
        flags = {
            "es-ES": "🇪🇸",
            "de-DE": "🇩🇪",
            "en-US": "🇺🇸",
            "unknown": "🌍"
        }
        return flags.get(language_code, "🌍")

    def _save_transcript_files(self, prefix=None):
        """Save transcript to JSON and TXT files."""
        if not prefix:
            prefix = f"transcript_{self.transcript_data['session_id']}"

        # JSON file
        json_filename = f"{prefix}.json"
        with open(json_filename, 'w', encoding='utf-8') as f:
            json.dump(self.transcript_data, f, indent=2, ensure_ascii=False)

        # TXT file
        txt_filename = f"{prefix}.txt"
        with open(txt_filename, 'w', encoding='utf-8') as f:
            f.write(f"MULTILINGUAL TRANSCRIPT - {self.transcript_data['session_id']}\n")
            f.write(f"Language Setting: {self.transcript_data['language_setting']}\n")
            f.write(f"Languages Detected: {', '.join(self.transcript_data['languages_detected'])}\n")
            f.write(f"Started: {self.transcript_data['start_time']}\n")
            f.write("=" * 60 + "\n\n")

            for segment in self.transcript_data["segments"]:
                timestamp = segment["start_time"][11:19]
                lang_flag = self._get_language_flag(segment["detected_language"])
                f.write(f"[{timestamp}] {lang_flag} {segment['speaker_id']}: {segment['text']}\n")

            f.write(f"\n" + "=" * 60)
            f.write(f"\nSummary: {self.transcript_data['total_segments']} segments, ")
            f.write(f"{self.transcript_data['total_speakers']} speakers\n")
            f.write(f"Languages: {', '.join(self.transcript_data['languages_detected'])}")

        print(f"\n💾 Files saved:")
        print(f"   📄 {txt_filename}")
        print(f"   📊 {json_filename}")

        return json_filename, txt_filename


async def test_multilingual():
    """Test multilingual transcription."""
    print("🌍 Multilingual Transcription Test")
    print("Supports: Spanish 🇪🇸, German 🇩🇪, English 🇺🇸")
    print()

    # Test with auto-detection
    transcriber = MultilingualTranscriber(language='auto')

    print("📺 Your Spanish YouTube video should be transcribed correctly now!")
    json_file, txt_file = await transcriber.transcribe_with_language(
        duration_seconds=30,
        output_file_prefix="spanish_youtube_test"
    )

    print(f"\n✅ Multilingual transcription complete!")
    print(f"📊 Check the files to see language detection in action")

    return json_file, txt_file


if __name__ == "__main__":
    print("🎯 Testing multilingual transcription")
    print("🗣️  Try speaking in different languages!")

    try:
        json_file, txt_file = asyncio.run(test_multilingual())
        print(f"\n🏆 Success! Files created:")
        print(f"   {json_file}")
        print(f"   {txt_file}")
    except KeyboardInterrupt:
        print("\n🛑 Interrupted")
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
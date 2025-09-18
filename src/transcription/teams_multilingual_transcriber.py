#!/usr/bin/env python3
"""Teams-compatible multilingual transcriber supporting Spanish, German, and English."""
import asyncio
import os
import json
import wave
import threading
from datetime import datetime, UTC
from typing import Optional, Callable, Dict, Any, List
from dotenv import load_dotenv
import azure.cognitiveservices.speech as speechsdk
try:
    import pyaudio
    PYAUDIO_AVAILABLE = True
except ImportError:
    PYAUDIO_AVAILABLE = False
    print("Warning: PyAudio not available. Audio recording disabled. Install with: pip install pyaudio")

load_dotenv()


class TeamsMultilingualTranscriber:
    """Teams-compatible transcriber with multilingual auto-detection and speaker diarization."""

    SUPPORTED_LANGUAGES = {
        'spanish': 'es-ES',
        'german': 'de-DE',
        'english': 'en-US',
        'auto': 'auto-detect'
    }

    def __init__(self, language='auto', on_transcription_callback: Optional[Callable] = None):
        """Initialize with language preference and callback."""
        self.speech_key = os.getenv("AZURE_SPEECH_KEY")
        self.speech_region = os.getenv("AZURE_SPEECH_REGION")
        self.language = language
        self.on_transcription_callback = on_transcription_callback
        self.recognizer = None
        self.is_transcribing = False

        # Speaker diarization state
        self.segment_counter = 0
        self.speaker_counter = 0
        self.last_speech_time = None

        # Session tracking
        self.session_id = f"teams_multilingual_{datetime.now(UTC).strftime('%Y%m%d_%H%M%S')}"
        self.session_start = datetime.now(UTC)
        self.transcript_segments: List[Dict[str, Any]] = []

        # Audio recording for corroboration
        self.audio_recording = PYAUDIO_AVAILABLE  # Enable only if PyAudio is available
        self.audio_frames = []
        self.audio_thread = None
        self.audio_stream = None
        self.recording_active = False

        # Audio settings (16kHz mono for Azure Speech compatibility)
        if PYAUDIO_AVAILABLE:
            self.audio_format = pyaudio.paInt16
        else:
            self.audio_format = None
        self.audio_channels = 1
        self.audio_rate = 16000
        self.audio_chunk = 1024

    async def start_transcription(self) -> None:
        """Start continuous transcription for Teams audio."""
        if self.is_transcribing:
            return

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
        else:
            # Set specific language
            speech_lang = self.SUPPORTED_LANGUAGES.get(self.language, 'en-US')
            speech_config.speech_recognition_language = speech_lang

            audio_config = speechsdk.AudioConfig(use_default_microphone=True)
            self.recognizer = speechsdk.SpeechRecognizer(
                speech_config=speech_config,
                audio_config=audio_config
            )

        # Enhanced settings for better recognition
        speech_config.set_property(speechsdk.PropertyId.SpeechServiceConnection_InitialSilenceTimeoutMs, "5000")
        speech_config.set_property(speechsdk.PropertyId.SpeechServiceConnection_EndSilenceTimeoutMs, "500")

        # Connect event handlers
        self.recognizer.recognized.connect(self._on_recognized)
        self.recognizer.recognizing.connect(self._on_recognizing)

        # Start audio recording if enabled
        if self.audio_recording:
            self._start_audio_recording()

        # Start continuous recognition
        self.recognizer.start_continuous_recognition()
        self.is_transcribing = True

    async def stop_transcription(self) -> Dict[str, Any]:
        """Stop transcription and return session summary."""
        if not self.is_transcribing or not self.recognizer:
            return {}

        self.recognizer.stop_continuous_recognition()
        self.is_transcribing = False

        # Stop audio recording
        if self.audio_recording:
            self._stop_audio_recording()

        session_summary = {
            "session_id": self.session_id,
            "start_time": self.session_start.isoformat(),
            "end_time": datetime.now(UTC).isoformat(),
            "language_setting": self.language,
            "total_segments": len(self.transcript_segments),
            "total_speakers": self.speaker_counter,
            "languages_detected": list(set([
                seg.get("detected_language", "unknown")
                for seg in self.transcript_segments
            ])),
            "segments": self.transcript_segments
        }

        return session_summary

    def _on_recognized(self, evt) -> None:
        """Handle speech recognition results."""
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

                # Speaker diarization (3+ second gap = new speaker)
                if (self.last_speech_time is None or
                    (current_time.timestamp() - self.last_speech_time) > 3):
                    self.speaker_counter += 1

                self.last_speech_time = current_time.timestamp()
                self.segment_counter += 1

                segment = {
                    "segment_id": self.segment_counter,
                    "speaker_id": f"Speaker_{self.speaker_counter}",
                    "text": text,
                    "detected_language": detected_language,
                    "start_time": current_time.isoformat(),
                    "confidence": 0.95,
                    "duration_ms": int(evt.result.duration / 10000),
                    "offset_ms": int(evt.result.offset / 10000)
                }

                self.transcript_segments.append(segment)

                # Call the callback if provided
                if self.on_transcription_callback:
                    asyncio.create_task(self.on_transcription_callback(segment))

    def _on_recognizing(self, evt) -> None:
        """Handle partial recognition results."""
        # This can be used for real-time display of partial results
        pass

    async def process_audio(self, audio_data: bytes) -> None:
        """Process audio data from Teams call stream."""
        # This method will be used when we integrate with Teams audio streams
        # For now, we're using microphone input for testing
        pass

    def get_language_flag(self, language_code: str) -> str:
        """Get emoji flag for language."""
        flags = {
            "es-ES": "🇪🇸",
            "de-DE": "🇩🇪",
            "en-US": "🇺🇸",
            "unknown": "🌍"
        }
        return flags.get(language_code, "🌍")

    async def save_transcript_files(self, prefix: Optional[str] = None) -> tuple:
        """Save transcript to JSON and TXT files."""
        if not prefix:
            prefix = f"teams_transcript_{self.session_id}"

        # Prepare transcript data
        transcript_data = {
            "session_id": self.session_id,
            "start_time": self.session_start.isoformat(),
            "end_time": datetime.now(UTC).isoformat(),
            "language_setting": self.language,
            "source": "teams_meeting",
            "segments": self.transcript_segments,
            "total_segments": len(self.transcript_segments),
            "total_speakers": self.speaker_counter,
            "languages_detected": list(set([
                seg.get("detected_language", "unknown")
                for seg in self.transcript_segments
            ]))
        }

        # JSON file
        json_filename = f"{prefix}.json"
        with open(json_filename, 'w', encoding='utf-8') as f:
            json.dump(transcript_data, f, indent=2, ensure_ascii=False)

        # TXT file
        txt_filename = f"{prefix}.txt"
        with open(txt_filename, 'w', encoding='utf-8') as f:
            f.write(f"TEAMS MULTILINGUAL TRANSCRIPT - {self.session_id}\n")
            f.write(f"Language Setting: {self.language}\n")
            f.write(f"Languages Detected: {', '.join(transcript_data['languages_detected'])}\n")
            f.write(f"Started: {self.session_start.isoformat()}\n")
            f.write("=" * 60 + "\n\n")

            for segment in self.transcript_segments:
                timestamp = segment["start_time"][11:19]
                lang_flag = self.get_language_flag(segment["detected_language"])
                f.write(f"[{timestamp}] {lang_flag} {segment['speaker_id']}: {segment['text']}\n")

            f.write(f"\n" + "=" * 60)
            f.write(f"\nSummary: {transcript_data['total_segments']} segments, ")
            f.write(f"{transcript_data['total_speakers']} speakers\n")
            f.write(f"Languages: {', '.join(transcript_data['languages_detected'])}")

        # Save audio file if available
        audio_filename = None
        if self.audio_recording and self.audio_frames:
            audio_filename = f"{prefix}.wav"
            self._save_audio_file(audio_filename)

        return json_filename, txt_filename, audio_filename

    def _start_audio_recording(self) -> None:
        """Start recording audio for corroboration."""
        if not PYAUDIO_AVAILABLE:
            return

        try:
            self.audio_frames = []
            self.recording_active = True

            # Initialize PyAudio
            audio = pyaudio.PyAudio()

            # Create audio stream
            self.audio_stream = audio.open(
                format=self.audio_format,
                channels=self.audio_channels,
                rate=self.audio_rate,
                input=True,
                frames_per_buffer=self.audio_chunk
            )

            # Start recording thread
            self.audio_thread = threading.Thread(target=self._record_audio)
            self.audio_thread.start()

        except Exception as e:
            print(f"Warning: Could not start audio recording: {e}")
            self.audio_recording = False

    def _record_audio(self) -> None:
        """Record audio in a separate thread."""
        while self.recording_active:
            try:
                data = self.audio_stream.read(self.audio_chunk, exception_on_overflow=False)
                self.audio_frames.append(data)
            except Exception:
                break

    def _stop_audio_recording(self) -> None:
        """Stop audio recording."""
        if self.recording_active:
            self.recording_active = False

            if self.audio_thread and self.audio_thread.is_alive():
                self.audio_thread.join(timeout=1.0)

            if self.audio_stream:
                self.audio_stream.stop_stream()
                self.audio_stream.close()

    def _save_audio_file(self, filename: str) -> None:
        """Save recorded audio to WAV file."""
        if not PYAUDIO_AVAILABLE:
            return

        try:
            with wave.open(filename, 'wb') as wf:
                wf.setnchannels(self.audio_channels)
                wf.setsampwidth(pyaudio.get_sample_size(self.audio_format))
                wf.setframerate(self.audio_rate)
                wf.writeframes(b''.join(self.audio_frames))

            print(f"🎵 Audio saved: {filename}")

        except Exception as e:
            print(f"Warning: Could not save audio file: {e}")
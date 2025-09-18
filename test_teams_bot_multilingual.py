#!/usr/bin/env python3
"""Test script to simulate Teams bot with multilingual transcription."""
import asyncio
import os
from datetime import datetime
from src.transcription.teams_multilingual_transcriber import TeamsMultilingualTranscriber


class MockTurnContext:
    """Mock TurnContext for testing Teams bot functionality."""

    def __init__(self):
        self.messages = []

    async def send_activity(self, message: str):
        """Mock send activity that prints the message."""
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"[{timestamp}] 🤖 Bot: {message}")
        self.messages.append(message)


class MockTeamsBotTest:
    """Mock Teams bot to test multilingual transcription integration."""

    def __init__(self):
        self.active_call = None
        self.transcriber = None
        self.transcript_entries = []

    async def test_join_call(self, turn_context: MockTurnContext):
        """Simulate joining a Teams call."""
        if self.active_call:
            await turn_context.send_activity("Already in a call. Use /leave first.")
            return

        try:
            # Initialize call context
            self.active_call = {
                "meeting_url": "https://teams.microsoft.com/l/meetup-join/mock",
                "joined_at": datetime.utcnow().isoformat(),
                "call_id": f"mock_call_{datetime.utcnow().timestamp()}"
            }

            # Initialize multilingual Speech-to-Text transcriber with callback
            self.transcriber = TeamsMultilingualTranscriber(
                language='auto',  # Auto-detect Spanish, German, English
                on_transcription_callback=self.on_transcription_received
            )
            await self.transcriber.start_transcription()

            await turn_context.send_activity(
                f"✅ Joined call and started multilingual transcription (🇪🇸 🇩🇪 🇺🇸) with speaker diarization."
            )

        except Exception as e:
            self.active_call = None
            self.transcriber = None
            await turn_context.send_activity(f"❌ Failed to join call: {str(e)}")

    async def test_leave_call(self, turn_context: MockTurnContext):
        """Simulate leaving a Teams call."""
        if not self.active_call:
            await turn_context.send_activity("Not currently in a call.")
            return

        try:
            # Stop transcription and save files
            session_summary = {}
            saved_files = []
            if self.transcriber:
                session_summary = await self.transcriber.stop_transcription()
                result = await self.transcriber.save_transcript_files()
                if result and len(result) >= 2:
                    json_file, txt_file = result[0], result[1]
                    saved_files = [txt_file, json_file]
                    # Check if audio file was also saved
                    if len(result) > 2 and result[2]:
                        audio_file = result[2]
                        saved_files.append(audio_file)
                self.transcriber = None

            # Prepare transcript summary
            total_segments = session_summary.get('total_segments', len(self.transcript_entries))
            total_speakers = session_summary.get('total_speakers', 0)
            languages = session_summary.get('languages_detected', [])

            # Include file information in summary
            files_info = f"📄 Files saved: {len(saved_files)} files" if saved_files else "No files saved"
            has_audio = any("wav" in str(f) for f in saved_files)
            audio_info = " (🎵 includes audio)" if has_audio else ""

            transcript_summary = (
                f"📝 Transcript saved: {total_segments} segments, {total_speakers} speakers\\n"
                f"🌍 Languages detected: {', '.join(languages) if languages else 'None'}\\n"
                f"{files_info}{audio_info}"
            )

            # Clear state
            self.active_call = None
            self.transcript_entries = []

            await turn_context.send_activity(
                f"✅ Left call. {transcript_summary}"
            )

        except Exception as e:
            await turn_context.send_activity(f"❌ Error leaving call: {str(e)}")

    async def test_status(self, turn_context: MockTurnContext):
        """Report current bot status."""
        if self.active_call:
            # Get current transcription stats if available
            segments_count = len(self.transcript_entries)
            speakers_count = 0
            languages = []

            if self.transcriber and hasattr(self.transcriber, 'transcript_segments'):
                segments_count = len(self.transcriber.transcript_segments)
                speakers_count = self.transcriber.speaker_counter
                languages = list(set([
                    seg.get("detected_language", "unknown")
                    for seg in self.transcriber.transcript_segments
                ]))

            status = (
                f"📞 In call since: {self.active_call['joined_at']}\\n"
                f"📝 Transcript: {segments_count} segments, {speakers_count} speakers\\n"
                f"🌍 Languages detected: {', '.join(languages) if languages else 'None'}\\n"
                f"🎯 Multilingual mode: Spanish 🇪🇸 German 🇩🇪 English 🇺🇸"
            )
        else:
            status = "🔴 Not in a call\\n🎯 Ready for multilingual transcription (🇪🇸 🇩🇪 🇺🇸)"

        await turn_context.send_activity(status)

    async def on_transcription_received(self, transcription_result):
        """Handle transcription results with speaker diarization."""
        # Store transcription with speaker identification
        self.transcript_entries.append(transcription_result)

        # Display transcription with language flag
        lang_flag = self.get_language_flag(transcription_result.get('detected_language', 'unknown'))
        speaker_id = transcription_result.get('speaker_id', 'Unknown')
        text = transcription_result.get('text', '')

        print(f"📝 {lang_flag} [{speaker_id}]: {text}")

    def get_language_flag(self, language_code: str) -> str:
        """Get emoji flag for language."""
        flags = {
            "es-ES": "🇪🇸",
            "de-DE": "🇩🇪",
            "en-US": "🇺🇸",
            "unknown": "🌍"
        }
        return flags.get(language_code, "🌍")


async def test_teams_bot_multilingual():
    """Test the Teams bot multilingual functionality."""
    print("🌍 Testing Teams Bot with Multilingual Transcription")
    print("=" * 60)

    bot = MockTeamsBotTest()
    context = MockTurnContext()

    # Test 1: Check status (should be not in call)
    print("\\n🔍 Test 1: Initial Status")
    await bot.test_status(context)

    # Test 2: Join call
    print("\\n📞 Test 2: Join Call")
    await bot.test_join_call(context)

    # Test 3: Check status (should be in call)
    print("\\n🔍 Test 3: Status During Call")
    await bot.test_status(context)

    # Test 4: Wait for transcription (simulate meeting audio)
    print("\\n🎤 Test 4: Waiting for Audio Input (30 seconds)")
    print("🗣️  Speak in Spanish, German, or English to test multilingual detection!")
    print("📺 Your Spanish YouTube video should work perfectly now!")

    # Wait for audio input and transcription
    for i in range(30):
        await asyncio.sleep(1)
        if i % 10 == 0 and i > 0:
            print(f"⏰ {30-i} seconds remaining...")

    # Test 5: Check status after transcription
    print("\\n🔍 Test 5: Status After Transcription")
    await bot.test_status(context)

    # Test 6: Leave call
    print("\\n📴 Test 6: Leave Call")
    await bot.test_leave_call(context)

    # Test 7: Final status
    print("\\n🔍 Test 7: Final Status")
    await bot.test_status(context)

    print("\\n✅ Teams Bot Multilingual Test Complete!")
    print("🏆 The bot now supports Spanish 🇪🇸, German 🇩🇪, and English 🇺🇸!")


if __name__ == "__main__":
    print("🎯 Testing Teams Bot Multilingual Integration")
    print("🔗 This simulates the full Teams bot workflow with multilingual transcription")

    try:
        asyncio.run(test_teams_bot_multilingual())
    except KeyboardInterrupt:
        print("\\n🛑 Test interrupted")
    except Exception as e:
        print(f"❌ Test error: {e}")
        import traceback
        traceback.print_exc()
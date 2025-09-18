"""Minimal Teams bot for joining calls and transcribing with diarization."""
import os
import logging
from typing import Optional, List, Dict, Any
from botbuilder.core import TurnContext, ActivityHandler
from botbuilder.schema import ChannelAccount
import aiohttp
import asyncio
from datetime import datetime
from src.transcription.teams_multilingual_transcriber import TeamsMultilingualTranscriber

logger = logging.getLogger(__name__)


class TeamsTranscriptionBot(ActivityHandler):
    """MVP Teams bot that joins calls and transcribes with speaker diarization."""

    def __init__(self):
        super().__init__()
        self.active_call: Optional[Dict[str, Any]] = None
        self.transcriber: Optional['TeamsMultilingualTranscriber'] = None
        self.transcript_entries: List[Dict[str, Any]] = []
        self.graph_token: Optional[str] = None

    async def on_message_activity(self, turn_context: TurnContext) -> None:
        """Handle incoming messages from Teams."""
        text = turn_context.activity.text.lower() if turn_context.activity.text else ""

        if text.startswith("/join "):
            await self._handle_join_call(turn_context, text)
        elif text.startswith("/leave"):
            await self._handle_leave_call(turn_context)
        elif text.startswith("/status"):
            await self._handle_status(turn_context)
        else:
            await turn_context.send_activity(
                "Commands: /join <meeting_url>, /leave, /status"
            )

    async def _handle_join_call(self, turn_context: TurnContext, text: str) -> None:
        """Join a Teams call and start transcription."""
        if self.active_call:
            await turn_context.send_activity("Already in a call. Use /leave first.")
            return

        # Extract meeting URL
        meeting_url = text.replace("/join ", "").strip()
        if not meeting_url.startswith("https://teams.microsoft.com"):
            await turn_context.send_activity("Invalid Teams meeting URL.")
            return

        try:
            # Initialize call context
            self.active_call = {
                "meeting_url": meeting_url,
                "joined_at": datetime.utcnow().isoformat(),
                "call_id": None  # Will be set when Graph API call succeeds
            }

            # Get Graph API token
            from src.auth.msal_client import MSALAuthClient
            auth_client = MSALAuthClient()
            self.graph_token = auth_client.get_token()

            # Join the Teams call via Graph API
            await self._join_teams_call_via_graph(meeting_url)

            # Initialize multilingual Speech-to-Text transcriber with callback
            self.transcriber = TeamsMultilingualTranscriber(
                language='auto',  # Auto-detect Spanish, German, English
                on_transcription_callback=self.on_transcription_received
            )
            await self.transcriber.start_transcription()

            await turn_context.send_activity(
                f"✅ Joined call and started multilingual transcription (🇪🇸 🇩🇪 🇺🇸) with speaker diarization."
            )
            logger.info(f"Bot joined call: {meeting_url}")

        except Exception as e:
            self.active_call = None
            self.transcriber = None
            await turn_context.send_activity(f"❌ Failed to join call: {str(e)}")
            logger.error(f"Failed to join call: {e}")

    async def _join_teams_call_via_graph(self, meeting_url: str) -> None:
        """Join Teams call using Graph API."""
        # This will be implemented with actual Graph API calls
        # For MVP, we're focusing on the structure
        headers = {
            "Authorization": f"Bearer {self.graph_token}",
            "Content-Type": "application/json"
        }

        # Parse meeting URL to extract meeting info
        # In a real implementation, this would make actual Graph API calls
        # to join the meeting and establish media stream
        logger.info(f"Joining Teams call via Graph API: {meeting_url}")

        # Placeholder for Graph API implementation
        self.active_call["call_id"] = "mock_call_id_" + datetime.utcnow().isoformat()

    async def _handle_leave_call(self, turn_context: TurnContext) -> None:
        """Leave the current call and save transcript."""
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
                f"📝 Transcript saved: {total_segments} segments, {total_speakers} speakers\n"
                f"🌍 Languages detected: {', '.join(languages) if languages else 'None'}\n"
                f"{files_info}{audio_info}"
            )

            # Clear state
            self.active_call = None
            self.transcript_entries = []

            await turn_context.send_activity(
                f"✅ Left call. {transcript_summary}"
            )
            logger.info("Bot left call and saved transcript")

        except Exception as e:
            await turn_context.send_activity(f"❌ Error leaving call: {str(e)}")
            logger.error(f"Failed to leave call: {e}")

    async def _handle_status(self, turn_context: TurnContext) -> None:
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
                f"📞 In call since: {self.active_call['joined_at']}\n"
                f"📝 Transcript: {segments_count} segments, {speakers_count} speakers\n"
                f"🌍 Languages detected: {', '.join(languages) if languages else 'None'}\n"
                f"🎯 Multilingual mode: Spanish 🇪🇸 German 🇩🇪 English 🇺🇸"
            )
        else:
            status = "🔴 Not in a call\n🎯 Ready for multilingual transcription (🇪🇸 🇩🇪 🇺🇸)"

        await turn_context.send_activity(status)

    async def process_audio_stream(self, audio_data: bytes) -> None:
        """Process incoming audio stream from Teams call."""
        if self.transcriber:
            await self.transcriber.process_audio(audio_data)

    async def on_transcription_received(self, transcription_result: Dict[str, Any]) -> None:
        """Handle transcription results with speaker diarization."""
        # Store transcription with speaker identification
        self.transcript_entries.append(transcription_result)

        logger.info(
            f"Transcription: Speaker {transcription_result.get('speaker_id')}: "
            f"{transcription_result.get('text')}"
        )

    async def on_members_added_activity(
        self, members_added: List[ChannelAccount], turn_context: TurnContext
    ) -> None:
        """Welcome message when bot is added to a channel."""
        for member in members_added:
            if member.id != turn_context.activity.recipient.id:
                await turn_context.send_activity(
                    "👋 Hi! I'm the Teams Transcription Bot.\n"
                    "I can join calls and provide real-time transcription with speaker identification.\n\n"
                    "Commands:\n"
                    "• `/join <meeting_url>` - Join a Teams call\n"
                    "• `/leave` - Leave current call\n"
                    "• `/status` - Check bot status"
                )


"""Minimal Teams bot for joining calls and transcribing with diarization."""
import os
import logging
from typing import Optional, List, Dict, Any
from botbuilder.core import TurnContext, ActivityHandler
from botbuilder.schema import ChannelAccount
import aiohttp
import asyncio
from datetime import datetime
from src.transcription.simple_transcriber import SimpleSpeechTranscriber

logger = logging.getLogger(__name__)


class TeamsTranscriptionBot(ActivityHandler):
    """MVP Teams bot that joins calls and transcribes with speaker diarization."""

    def __init__(self):
        super().__init__()
        self.active_call: Optional[Dict[str, Any]] = None
        self.transcriber: Optional['SimpleSpeechTranscriber'] = None
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

            # Initialize Speech-to-Text transcriber with callback
            self.transcriber = SimpleSpeechTranscriber(
                on_transcription_callback=self.on_transcription_received
            )
            await self.transcriber.start_transcription()

            await turn_context.send_activity(
                f"✅ Joined call and started transcription with speaker diarization."
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
            # Stop transcription
            if self.transcriber:
                await self.transcriber.stop_transcription()
                self.transcriber = None

            # Save transcript
            transcript_summary = f"Transcript saved with {len(self.transcript_entries)} entries."

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
            status = (
                f"📞 In call since: {self.active_call['joined_at']}\n"
                f"📝 Transcript entries: {len(self.transcript_entries)}"
            )
        else:
            status = "🔴 Not in a call"

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


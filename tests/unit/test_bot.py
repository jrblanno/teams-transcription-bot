"""Test Teams bot MVP functionality - Join call and transcribe."""
import pytest
from unittest.mock import AsyncMock, Mock, patch
import asyncio
from src.bot.teams_bot import TeamsTranscriptionBot


class TestTeamsTranscriptionBotMVP:
    """Test MVP bot functionality: join call, stream audio, transcribe."""

    @pytest.mark.asyncio
    async def test_bot_joins_teams_call(self):
        """Test bot can join a Teams call when given meeting URL."""
        # Arrange
        bot = TeamsTranscriptionBot()
        meeting_url = "https://teams.microsoft.com/l/meetup-join/19:meeting_abc123"
        turn_context = Mock()
        turn_context.activity.text = f"/join {meeting_url}"
        turn_context.send_activity = AsyncMock()

        # Act
        await bot.on_message_activity(turn_context)

        # Assert
        turn_context.send_activity.assert_called()
        assert bot.active_call is not None
        assert bot.active_call["meeting_url"] == meeting_url

    @pytest.mark.asyncio
    async def test_bot_starts_transcription_on_join(self):
        """Test bot starts transcription when joining a call."""
        # Arrange
        bot = TeamsTranscriptionBot()
        meeting_url = "https://teams.microsoft.com/l/meetup-join/19:meeting_abc123"

        with patch('src.bot.teams_bot.SimpleSpeechTranscriber') as MockTranscriber:
            mock_transcriber = MockTranscriber.return_value
            mock_transcriber.start_transcription = AsyncMock()

            turn_context = Mock()
            turn_context.activity.text = f"/join {meeting_url}"
            turn_context.send_activity = AsyncMock()

            # Act
            await bot.on_message_activity(turn_context)

            # Assert
            mock_transcriber.start_transcription.assert_called_once()
            assert bot.transcriber is not None

    @pytest.mark.asyncio
    async def test_bot_handles_audio_stream(self):
        """Test bot receives audio stream and sends to Speech-to-Text."""
        # Arrange
        bot = TeamsTranscriptionBot()
        audio_data = b"mock_audio_data"

        with patch('src.bot.teams_bot.SimpleSpeechTranscriber') as MockTranscriber:
            mock_transcriber = MockTranscriber.return_value
            mock_transcriber.process_audio = AsyncMock()
            bot.transcriber = mock_transcriber

            # Act
            await bot.process_audio_stream(audio_data)

            # Assert
            mock_transcriber.process_audio.assert_called_once_with(audio_data)

    @pytest.mark.asyncio
    async def test_bot_receives_transcription_with_diarization(self):
        """Test bot receives transcribed text with speaker identification."""
        # Arrange
        bot = TeamsTranscriptionBot()
        transcription_result = {
            "speaker_id": "Speaker_1",
            "text": "Hello, this is a test",
            "timestamp": "2024-01-01T12:00:00Z"
        }

        # Act
        await bot.on_transcription_received(transcription_result)

        # Assert
        assert len(bot.transcript_entries) == 1
        assert bot.transcript_entries[0]["speaker_id"] == "Speaker_1"
        assert bot.transcript_entries[0]["text"] == "Hello, this is a test"

    @pytest.mark.asyncio
    async def test_bot_leaves_call_and_saves_transcript(self):
        """Test bot leaves call and saves the transcript."""
        # Arrange
        bot = TeamsTranscriptionBot()
        bot.active_call = Mock(meeting_url="https://teams.microsoft.com/test")
        bot.transcript_entries = [
            {"speaker_id": "Speaker_1", "text": "Test message", "timestamp": "2024-01-01T12:00:00Z"}
        ]

        turn_context = Mock()
        turn_context.activity.text = "/leave"
        turn_context.send_activity = AsyncMock()

        # Act
        await bot.on_message_activity(turn_context)

        # Assert
        turn_context.send_activity.assert_called()
        assert bot.active_call is None
        assert len(bot.transcript_entries) == 0  # Transcript cleared after saving
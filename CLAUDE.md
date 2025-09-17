# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Teams Transcription Bot - A Python-based Microsoft Teams bot that joins meetings to provide real-time transcription with speaker diarization. The bot captures audio from both remote participants and in-room audio feeds, processes it through Azure Speech-to-Text, and stores transcripts securely.

## Critical Security Requirements

**MANDATORY**: All Azure credentials MUST be read from the `.env` file. This project uses Azure System Assigned Managed Identities - NEVER hardcode credentials anywhere in the codebase.

## Development Commands

### Testing
```bash
# Run all tests with TDD approach
pytest

# Run with coverage report
pytest --cov=src --cov-report=html

# Run specific test file
pytest tests/test_project_structure.py -v

# Run tests for a specific module
pytest tests/unit/test_bot.py -v
```

### Development Setup
```bash
# Create and activate virtual environment
python -m venv venv
source venv/bin/activate  # macOS/Linux
venv\Scripts\activate     # Windows

# Install dependencies
pip install -r requirements.txt

# Install package in development mode
pip install -e .
```

### Code Quality
```bash
# Format code with black
black src/ tests/

# Run linter
flake8 src/ tests/

# Type checking
mypy src/

# Run all quality checks
black src/ tests/ && flake8 src/ tests/ && mypy src/
```

### Running the Bot
```bash
# Start the bot (after configuration)
python -m src.bot.main
```

## Architecture & Module Organization

The codebase follows a feature-based vertical slicing architecture with clear module boundaries:

### Core Modules

**src/bot/** - Teams bot implementation
- Handles Teams channel interactions via Bot Framework SDK
- Manages meeting join/leave lifecycle
- Processes Teams activities and events

**src/graph_api/** - Microsoft Graph API integration
- MSAL authentication with OAuth2 client credentials flow
- Meeting management (join, media access)
- RTP audio packet handling from Teams

**src/audio/** - Audio processing pipeline
- Stream handling and buffering from multiple sources
- Format conversion (RTP to WAV)
- Audio mixing for hybrid scenarios (remote + in-room)
- Virtual audio cable integration for physical microphones

**src/transcription/** - Azure Speech-to-Text integration
- Conversation transcriber with speaker diarization
- Continuous recognition handlers
- Transcript processing and formatting

**src/storage/** - Transcript persistence (planned)
- Azure Blob Storage client
- Transcript organization by meeting/date

### Infrastructure

**terraform/** - Infrastructure as Code
- Azure resource provisioning (Bot Service, Cognitive Services, Key Vault, Storage)
- Managed Identity configuration
- Environment-specific configurations in `terraform/environments/`

## Implementation Roadmap (GitHub Issue #1)

The project follows a 12-task implementation plan with TDD methodology:

1. ✅ **Project Setup and Structure** - Complete
2. **Terraform Infrastructure Setup** - Azure resources provisioning
3. **Azure AD App Registration** - Graph API permissions configuration
4. **Bot Framework Implementation** - Core bot functionality
5. **Graph API Integration** - Meeting join and media access
6. **Audio Processing Pipeline** - Stream handling and conversion
7. **In-Room Audio Integration** - Virtual cable support
8. **Azure Speech-to-Text Integration** - Transcription with diarization
9. **Transcript Storage** - Blob storage management
10. **Teams Integration** - Adaptive cards and notifications
11. **Testing Infrastructure** - Unit/integration tests
12. **Monitoring and Logging** - Application Insights integration

## Key Technical Decisions

### Authentication Strategy
- Uses Azure AD Service Principal with client credentials flow
- System Assigned Managed Identities for Azure resource access
- All credentials loaded from environment variables via python-dotenv

### Async Architecture
- Entire codebase uses async/await patterns for concurrent meeting support
- aiohttp for async HTTP operations
- Designed to handle 10+ concurrent meetings

### Audio Processing
- RTP packet reception from Teams Graph API
- Audio buffering with configurable buffer size (default: 5 seconds)
- Format: 16kHz sample rate, mono channel for optimal transcription

### Testing Strategy
- TDD approach: RED → GREEN → REFACTOR cycle
- Minimum 90% test coverage requirement
- Comprehensive mocking for external services

## Environment Configuration

The `.env` file must contain:
- Azure AD credentials (AZURE_CLIENT_ID, AZURE_TENANT_ID, AZURE_CLIENT_SECRET)
- Azure subscription details (AZURE_SUBSCRIPTION_ID, AZURE_RESOURCE_GROUP)
- Speech service configuration (AZURE_SPEECH_KEY, AZURE_SPEECH_REGION)
- Bot Framework credentials (BOT_APP_ID, BOT_APP_PASSWORD)

Reference `.env.example` for the complete template.

## Graph API Permissions Required

The Azure AD app registration needs these Microsoft Graph permissions:
- Calls.AccessMedia.All
- Calls.JoinGroupCall.All
- Calls.InitiateGroupCall.All
- OnlineMeetings.ReadWrite

## Working with GitHub Issues

```bash
# View main implementation issue
gh issue view 1

# List all issues
gh issue list

# Check issue status
gh issue status
```

## Performance Targets

- Transcription latency: < 5 seconds
- Concurrent meetings: 10+ support
- Uptime: 99.9% SLA
- Test coverage: 90%+ for all new code
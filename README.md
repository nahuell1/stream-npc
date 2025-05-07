# Stream NPC

A real-time Twitch chat bot that listens to stream audio, transcribes it, and engages in natural conversation with the streamer. The bot uses Whisper for speech-to-text transcription and either Ollama or OpenAI for natural language generation.

## Features

- Real-time audio capture from Twitch streams
- Speech-to-text transcription using Whisper
- Natural language generation using Ollama or OpenAI
- WebSocket-based real-time updates
- Docker support for easy deployment
- Configurable AI providers and models
- Category-specific conversation styles
- Memory system for context-aware responses

## Prerequisites

### For Docker Deployment
- Docker and Docker Compose
- NVIDIA GPU with CUDA support (optional, for GPU acceleration)
- NVIDIA Container Toolkit (if using GPU)

### For Local Development
- Python 3.11+
- FFmpeg
- Ollama (for local LLM support) or OpenAI API key

## Installation

Choose one of the following installation methods:

### Option 1: Docker Deployment (Recommended)

1. Clone the repository:
```bash
git clone https://github.com/nahuell1/stream_npc.git
cd stream_npc
```

2. Create a `.env` file with your configuration:
```env
TWITCH_CHANNEL=your_channel
TWITCH_BOT_TOKEN=your_bot_token
TWITCH_CLIENT_ID=your_client_id
TWITCH_CLIENT_SECRET=your_client_secret
AI_PROVIDER=ollama  # or openai
OLLAMA_MODEL=llama2  # if using ollama
OPENAI_API_KEY=your_api_key  # if using openai
```

3. Build and run with Docker Compose:
```bash
docker-compose up --build
```

### Option 2: Local Development

1. Clone the repository:
```bash
git clone https://github.com/yourusername/stream_npc.git
cd stream_npc
```

2. Create and activate a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Create a `.env` file with your configuration (same as Docker option)

5. Start the server:
```bash
uvicorn app.main:app --reload
```

## Configuration

### Environment Variables

Required variables:
- `TWITCH_CHANNEL`: Your Twitch channel name
- `TWITCH_BOT_TOKEN`: Your Twitch bot OAuth token
- `TWITCH_CLIENT_ID`: Your Twitch application client ID
- `TWITCH_CLIENT_SECRET`: Your Twitch application client secret

AI Provider settings (choose one):
- For Ollama:
  - `AI_PROVIDER=ollama`
  - `OLLAMA_MODEL`: Model name (default: llama2)
- For OpenAI:
  - `AI_PROVIDER=openai`
  - `OPENAI_API_KEY`: Your OpenAI API key

Whisper settings:
- `WHISPER_MODEL`: Model size (tiny, base, small, medium, large)
- `USE_CUDA`: Enable GPU acceleration (true/false)
- `WHISPER_BEAM_SIZE`: Beam size for transcription (default: 1)
- `WHISPER_BEST_OF`: Number of candidates (default: 1)
- `WHISPER_TEMPERATURE`: Sampling temperature (default: 0.0)
- `WHISPER_CONDITION_PREVIOUS`: Use previous text (default: false)
- `WHISPER_MIN_CONFIDENCE`: Minimum confidence threshold (default: 0.5)

### API Endpoints

REST Endpoints:
- `GET /health`: Health check endpoint
- `POST /set-category/{category}`: Update the current Twitch category
  - Input: Category name in URL path
  - Output: JSON with status and category

WebSocket Endpoints:
- `WebSocket /ws/questions`: Real-time updates for generated questions
  - Connects to receive live updates of bot responses
  - No authentication required

## Architecture

The application consists of several key components:

1. **Audio Capture**: Uses Streamlink and FFmpeg to capture Twitch stream audio
2. **Transcription**: Whisper model for speech-to-text conversion
3. **Memory System**: Maintains conversation context
4. **Language Generation**: Ollama or OpenAI for natural responses
5. **Chat Integration**: TwitchIO for chat interaction
6. **Web Interface**: FastAPI for API endpoints and WebSocket updates

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

from dotenv import load_dotenv
load_dotenv()

import os
import asyncio
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%H:%M:%S'
)

from fastapi import FastAPI, WebSocket
from app.config import settings
from app.services.chat_bot import TwitchChatSender
from app.services.twitch_audio import TwitchAudioStreamer
from workers.transcriber import transcribe_worker
from app.memory import add_to_memory, get_recent_context
from app.generators.ollama_generator import OllamaGenerator
from app.generators.openai_generator import OpenAIGenerator

logger = logging.getLogger(__name__)
app = FastAPI()
ws_clients: set[WebSocket] = set()

chat_sender = TwitchChatSender()

def get_generator():
    provider = os.getenv("AI_PROVIDER", "ollama").lower()
    logger.info(f"Selected AI provider: {provider}")
    if provider == "ollama":
        return OllamaGenerator()
    elif provider == "openai":
        return OpenAIGenerator()
    else:
        raise ValueError(f"Unrecognized AI provider: {provider}")

generator = get_generator()

class WSManager:
    async def connect(self, ws: WebSocket):
        logger.info("WebSocket connection request received")
        await ws.accept()
        ws_clients.add(ws)
        logger.info(f"WebSocket connected, total clients: {len(ws_clients)}")

    async def disconnect(self, ws: WebSocket):
        ws_clients.remove(ws)
        logger.info(f"WebSocket disconnected, total clients: {len(ws_clients)}")

    async def broadcast(self, msg: str):
        for ws in list(ws_clients):
            try:
                logger.debug(f"Broadcasting message: {msg}")
                await ws.send_text(msg)
            except Exception:
                logger.warning("WebSocket send failed, disconnecting client")
                await self.disconnect(ws)

ws_manager = WSManager()

@app.post("/set-category/{category}")
async def set_category(category: str):
    """Update the current Twitch category.
    
    Args:
        category: The new Twitch category name
    """
    logger.info(f"Setting category to: {category}")
    if isinstance(generator, OllamaGenerator):
        generator.set_category(category)
    return {"status": "success", "category": category}

@app.on_event("startup")
async def startup():
    logger.info("Starting application...")
    queue = asyncio.Queue()

    # Initialize chat bot
    task_bot = asyncio.create_task(chat_sender.start())
    logger.info(f"Chat sender task created: {task_bot}")

    # Send test message
    async def test_msg():
        await asyncio.sleep(0.5)
        await chat_sender.send("🤖 [Test] Chat bot successfully connected!")
    task_test = asyncio.create_task(test_msg())
    logger.info(f"Test message task created: {task_test}")

    # Initialize audio streamer
    try:
        streamer = TwitchAudioStreamer(channel=settings.twitch_channel, queue=queue)
        task_stream = asyncio.create_task(streamer.start())
        logger.info(f"Audio streamer task created: {task_stream}")
    except Exception as e:
        logger.warning(f"Failed to start TwitchAudioStreamer: {e}")

    # Initialize transcriber
    task_worker = asyncio.create_task(transcribe_worker(queue, chat_sender))
    logger.info(f"Transcriber worker task created: {task_worker}")

    logger.info("Application startup complete")

@app.websocket("/ws/questions")
async def questions_ws(ws: WebSocket):
    await ws_manager.connect(ws)
    try:
        while True:
            await ws.receive_text()
    finally:
        await ws_manager.disconnect(ws)

@app.on_event("shutdown")
async def shutdown():
    logger.info("Shutting down application...")
    await chat_sender.stop()
    logger.info("Application shutdown complete")

@app.get("/health")
async def health_check():
    """Health check endpoint for monitoring."""
    return {"status": "healthy"}

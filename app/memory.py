from collections import deque
from dataclasses import dataclass
from datetime import datetime, timedelta
import logging
from typing import List, Dict

logger = logging.getLogger(__name__)

@dataclass
class MemoryEntry:
    """A single entry in the conversation memory.
    
    Attributes:
        timestamp: When the message was recorded
        speaker: Who said the message ('streamer' or 'bot')
        text: The actual message content
    """
    timestamp: datetime
    speaker: str
    text: str

    def __str__(self) -> str:
        time_str = self.timestamp.strftime("%H:%M:%S")
        return f"[{time_str}] {self.speaker}: {self.text}"

# In-memory storage for recent messages
messages: List[Dict] = []
MAX_MESSAGES = 10  # Keep last 10 messages
MAX_AGE = timedelta(minutes=5)  # Messages older than 5 minutes are removed

def add_to_memory(text: str, speaker: str = "user"):
    """Add a message to memory.
    
    Args:
        text: The message text
        speaker: Who said the message (user, streamer, or bot)
    """
    logger.info(f"Adding to memory - Speaker: {speaker}, Text: {text}")
    messages.append({
        "text": text,
        "speaker": speaker,
        "timestamp": datetime.now()
    })
    cleanup_old_messages()

def add_bot_question(question: str):
    """Add a bot question to memory.
    
    Args:
        question: The question asked by the bot
    """
    logger.info(f"Adding bot question to memory: {question}")
    add_to_memory(question, speaker="bot")

def cleanup_old_messages():
    """Remove messages older than MAX_AGE and keep only MAX_MESSAGES."""
    now = datetime.now()
    global messages
    messages = [
        msg for msg in messages
        if now - msg["timestamp"] <= MAX_AGE
    ]
    if len(messages) > MAX_MESSAGES:
        messages = messages[-MAX_MESSAGES:]
    logger.debug(f"Memory cleaned up. Current message count: {len(messages)}")

def get_recent_context() -> str:
    """Get recent conversation context.
    
    Returns:
        A string containing recent messages in chronological order
    """
    cleanup_old_messages()
    context = "\n".join(
        f"{msg['speaker']}: {msg['text']}"
        for msg in messages
    )
    logger.info(f"Generated context:\n{context}")
    return context

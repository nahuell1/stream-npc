import asyncio
import logging
import os
from aiohttp.client_exceptions import ClientConnectionResetError
from twitchio import Client

logger = logging.getLogger(__name__)

class TwitchChatSender:
    """Asynchronous queue for Twitch IRC chat messages.
    
    Implements rate limiting for verified bots (20 messages per 30 seconds).
    """
    def __init__(self):
        self.token = os.getenv("TWITCH_BOT_TOKEN")
        self.channel = os.getenv("TWITCH_CHANNEL")  # without '#'
        logger.info(f"Initializing chat bot - token: {'set' if self.token else 'missing'}, channel: {self.channel}")
        if not all([self.token, self.channel]):
            raise RuntimeError("Missing TWITCH_BOT_TOKEN or TWITCH_CHANNEL in .env")

        self.client = Client(
            token=self.token,
            initial_channels=[f"#{self.channel}"]
        )
        self.queue: asyncio.Queue[str] = asyncio.Queue()
        self._task: asyncio.Task | None = None

    async def start(self):
        logger.info("Starting chat bot")
        try:
            logger.info("Connecting to IRC...")
            await self.client.connect()
            logger.info("Connected, scheduling consumer...")
            self._task = asyncio.create_task(self._consumer())
            logger.info("Consumer task created")
        except ClientConnectionResetError:
            logger.warning("Client connection reset, ignoring")
        except Exception as exc:
            logger.error(f"Error starting TwitchChatSender: {exc}")

    async def stop(self):
        logger.info("Stopping chat bot")
        if self._task:
            self._task.cancel()
        await self.client.close()
        logger.info("Chat bot stopped")

    async def send(self, message: str):
        logger.debug(f"Enqueueing message: {message}")
        await self.queue.put(message)

    async def _consumer(self):
        logger.info("Consumer started")
        RATE, WINDOW = 20, 30
        bucket: list[float] = []

        # Wait for connect() to complete JOIN
        while not self.client.connected_channels:
            logger.debug("Waiting for connected channels...")
            await asyncio.sleep(0.1)

        logger.info(f"Connected to channels: {self.client.connected_channels}")
        while True:
            msg = await self.queue.get()
            logger.debug(f"Processing message from queue: {msg}")
            try:
                now = asyncio.get_event_loop().time()
                bucket = [t for t in bucket if now - t < WINDOW]
                if len(bucket) >= RATE:
                    wait = WINDOW - (now - bucket[0])
                    logger.info(f"Rate limit reached, sleeping {wait}s")
                    await asyncio.sleep(wait)
                    bucket = [t for t in bucket if now - t < WINDOW]
                logger.debug(f"Sending to channel #{self.channel}: {msg}")
                await self.client.connected_channels[0].send(msg)
                bucket.append(asyncio.get_event_loop().time())
            except Exception as exc:
                logger.error(f"Error sending message to chat: {exc}")

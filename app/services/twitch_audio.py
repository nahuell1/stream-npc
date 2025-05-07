import asyncio, logging, subprocess, streamlink
from pathlib import Path

log = logging.getLogger(__name__)

class TwitchAudioStreamer:
    """
    Descarga audio en tiempo real usando Streamlink + FFmpeg y
    va escribiendo chunks WAV en una cola asyncio.Queue()
    """

    def __init__(self, channel: str, queue: asyncio.Queue, sample_rate=16000):
        self.channel = channel
        self.queue = queue
        self.sample_rate = sample_rate
        self.proc: subprocess.Popen | None = None

    async def start(self):
        """Arranca la descarga ↔ transformación ↔ push a la cola"""
        log.info("Resolviendo stream HLS de twitch.tv/%s …", self.channel)
        streams = streamlink.streams(f"https://twitch.tv/{self.channel}")
        stream = streams.get("audio_only") or streams["best"]

        cmd = (
            stream.to_url(),  # HLS URL
            "-i", "pipe:0",
            "-ac", "1",
            "-ar", str(self.sample_rate),
            "-f", "wav",
            "pipe:1",
        )

        self.proc = subprocess.Popen(
            ["ffmpeg", "-loglevel", "quiet", "-i", stream.to_url(),
             "-ac", "1", "-ar", str(self.sample_rate), "-f", "wav", "pipe:1"],
            stdout=subprocess.PIPE,
            bufsize=0,
        )

        log.info("Streaming audio…")
        while True:
            data = self.proc.stdout.read(4096)  # 256 ms @ 16 kHz
            if not data:
                break
            await self.queue.put(data)

    async def stop(self):
        if self.proc and self.proc.poll() is None:
            self.proc.terminate()
            await asyncio.sleep(0.5)
            if self.proc.poll() is None:
                self.proc.kill()

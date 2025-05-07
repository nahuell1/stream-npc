import asyncio
import logging
import streamlink
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

class TwitchAudioStreamer:
    """Streams audio from a Twitch channel and publishes WAV bytes to an asyncio.Queue().
    """
    def __init__(self, channel: str, queue: asyncio.Queue, sample_rate: int = 16000):
        self.channel = channel
        self.queue = queue
        self.sample_rate = sample_rate
        self.proc: asyncio.subprocess.Process | None = None
        self.session = streamlink.Streamlink()
        logger.info(f"Initializing streamer for channel: {channel}")

    async def start(self):
        logger.info("Starting audio streamer")
        try:
            logger.info(f"Resolving streams for {self.channel}...")
            url = f"https://twitch.tv/{self.channel}"
            
            # Configure streamlink session
            self.session.set_option("http-headers", {
                "Client-ID": "kimne78kx3ncx6brgo4mv6wki5h1ko",
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
            })
            
            # Get available streams
            streams = self.session.streams(url)
            logger.info(f"Available qualities: {list(streams.keys())}")
            
            if not streams:
                raise RuntimeError(f"Channel {self.channel} is not live.")
                
            # Try to get audio_only stream first, then fallback to best
            stream = (
                streams.get("audio_only")
                or streams.get("best")
                or next(iter(streams.values()))
            )
            logger.info(f"Selected stream: {stream}")

            # Build ffmpeg command
            cmd = [
                "ffmpeg",
                "-loglevel", "warning",  # Changed from quiet to warning to see errors
                "-i", stream.to_url(),
                "-ac", "1",
                "-ar", str(self.sample_rate),
                "-f", "wav",
                "-"  # Output to stdout
            ]
            
            logger.info(f"Starting FFmpeg with command: {' '.join(cmd)}")
            
            # Start ffmpeg process
            self.proc = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            logger.info("FFmpeg subprocess started")

            # Start error monitoring task
            asyncio.create_task(self._monitor_errors())

            # Read audio data
            while True:
                try:
                    data = await self.proc.stdout.read(4096)
                    if not data:
                        logger.warning("No more data from FFmpeg, exiting loop")
                        break
                        
                    logger.debug(f"Received audio chunk of size: {len(data)} bytes")
                    await self.queue.put(data)
                    
                except Exception as e:
                    logger.error(f"Error reading from FFmpeg: {str(e)}", exc_info=True)
                    break
                    
        except Exception as exc:
            logger.error(f"TwitchAudioStreamer failed: {exc}", exc_info=True)
            raise
        finally:
            await self.stop()

    async def _monitor_errors(self):
        """Monitor FFmpeg stderr for errors."""
        if not self.proc or not self.proc.stderr:
            return
            
        try:
            while True:
                error = await self.proc.stderr.read(1024)
                if not error:
                    break
                error_text = error.decode().strip()
                if error_text:
                    logger.error(f"FFmpeg error: {error_text}")
        except Exception as e:
            logger.error(f"Error monitoring FFmpeg stderr: {str(e)}", exc_info=True)

    async def stop(self):
        """Stop the audio streamer and clean up resources."""
        logger.info("Stopping audio streamer")
        if self.proc and self.proc.returncode is None:
            try:
                self.proc.terminate()
                await asyncio.sleep(0.5)
                if self.proc.returncode is None:
                    self.proc.kill()
                logger.info("Subprocess terminated")
            except Exception as e:
                logger.error(f"Error stopping subprocess: {str(e)}", exc_info=True)
        
        # Clean up streamlink session
        try:
            self.session.close()
        except Exception as e:
            logger.error(f"Error closing streamlink session: {str(e)}", exc_info=True)

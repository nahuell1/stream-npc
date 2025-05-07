import asyncio
import logging
import os
import io
import wave
from faster_whisper import WhisperModel
from app.memory import add_to_memory, get_recent_context, add_bot_question
from app.services.chat_bot import TwitchChatSender
from app.generators.ollama_generator import OllamaGenerator
from app.generators.openai_generator import OpenAIGenerator

logger = logging.getLogger(__name__)
logger.info("Transcriber module loaded")

# Load configuration from environment variables with defaults for notebook
WHISPER_MODEL = os.getenv("WHISPER_MODEL", "base")  # Options: tiny, base, small, medium, large
USE_CUDA = os.getenv("USE_CUDA", "false").lower() == "true"
DEVICE = "cuda" if USE_CUDA else "cpu"
BEAM_SIZE = int(os.getenv("WHISPER_BEAM_SIZE", "1"))  # Default to 1 for faster processing
BEST_OF = int(os.getenv("WHISPER_BEST_OF", "1"))  # Default to 1 for faster processing
TEMPERATURE = float(os.getenv("WHISPER_TEMPERATURE", "0.0"))
CONDITION_ON_PREVIOUS = os.getenv("WHISPER_CONDITION_PREVIOUS", "false").lower() == "true"
INITIAL_PROMPT = os.getenv("WHISPER_INITIAL_PROMPT", "League of Legends, video games, gaming, streamer")

provider = os.getenv("AI_PROVIDER", "ollama")
logger.info(f"Using AI provider: {provider}")
if provider == "openai":
    generator = OpenAIGenerator()
else:
    generator = OllamaGenerator()

# Initialize Whisper with configured settings
model = WhisperModel(
    WHISPER_MODEL,
    device=DEVICE,
    compute_type="int8" if not USE_CUDA else "float16"  # Use int8 for CPU, float16 for GPU
)
logger.info(f"WhisperModel loaded: {WHISPER_MODEL} on {DEVICE}")

async def transcribe_worker(queue: asyncio.Queue, chat_sender: TwitchChatSender):
    logger.info("Starting transcriber worker")
    buffer = b""
    window_ms = 15000  # Increased to 15 seconds
    overlap_ms = 5000  # 5 second overlap
    last_emit = asyncio.get_running_loop().time()
    min_buffer_size = 16000 * 2 * 5  # Minimum 5 seconds of audio (16kHz, 16-bit)

    while True:
        try:
            # Wait for data in queue
            chunk = await queue.get()
            logger.debug(f"Received audio chunk of size: {len(chunk)} bytes")
            
            # Accumulate PCM bytes
            buffer += chunk
            now = asyncio.get_running_loop().time()
            buffer_duration = len(buffer) / (16000 * 2)  # Duration in seconds
            logger.debug(f"Current buffer duration: {buffer_duration:.2f} seconds")

            # Process window if enough time has passed and we have enough data
            if (now - last_emit) * 1000 >= window_ms and len(buffer) >= min_buffer_size:
                logger.info(f"Processing audio window of {len(buffer)} bytes")
                last_emit = now
                
                # Keep overlap in buffer
                overlap_bytes = int(overlap_ms * 16000 * 2 / 1000)  # Convert ms to bytes
                current_buffer = buffer[:-overlap_bytes] if len(buffer) > overlap_bytes else buffer
                buffer = buffer[-overlap_bytes:] if len(buffer) > overlap_bytes else b""
                
                logger.debug("Starting transcription...")
                segments, info = await asyncio.to_thread(transcribe_wav_bytes, current_buffer)
                logger.debug(f"Transcription completed. Got {len(segments)} segments")
                
                if segments:
                    # Combine all segments into a single text
                    text = " ".join(seg.text for seg in segments)
                    logger.info(f"Transcription: {text}")
                    
                    # Only process non-empty transcriptions
                    if text.strip():
                        add_to_memory(text, speaker="streamer")
                        context = get_recent_context()
                        logger.info(f"Context for question:\n{context}")
                        question = await asyncio.to_thread(generator.generate_question, context)
                        logger.info(f"Generated question: {question}")
                        add_bot_question(question)
                        await chat_sender.send(question)
            else:
                logger.debug(f"Waiting for more data. Current buffer: {len(buffer)} bytes, min required: {min_buffer_size} bytes")
        except Exception as e:
            logger.error(f"Error in transcribe_worker: {str(e)}", exc_info=True)

def transcribe_wav_bytes(pcm_bytes: bytes) -> tuple[list, dict]:
    """Transcribe WAV audio bytes to text.
    
    Args:
        pcm_bytes: Raw PCM audio data
        
    Returns:
        Tuple of (segments, info) from Whisper
    """
    try:
        # Build WAV in memory from raw PCM
        bio = io.BytesIO()
        with wave.open(bio, 'wb') as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)  # 16-bit samples
            wf.setframerate(16000)
            wf.writeframes(pcm_bytes)
        wav_data = bio.getvalue()
        
        logger.debug(f"Created WAV file of size: {len(wav_data)} bytes")
        
        # Decode with faster-whisper from BytesIO
        audio_buffer = io.BytesIO(wav_data)
        logger.debug("Starting Whisper transcription...")
        segments, info = model.transcribe(
            audio_buffer,
            language="es",
            vad_filter=True,
            vad_parameters=dict(
                min_silence_duration_ms=500,  # Minimum silence duration to consider a segment
                speech_pad_ms=100,  # Padding around speech segments
            ),
            beam_size=BEAM_SIZE,
            best_of=BEST_OF,
            temperature=TEMPERATURE,
            condition_on_previous_text=CONDITION_ON_PREVIOUS,
            initial_prompt=INITIAL_PROMPT
        )
        
        logger.debug(f"Whisper transcription completed. Info: {info}")
        return list(segments), info
    except Exception as e:
        logger.error(f"Error in transcribe_wav_bytes: {str(e)}", exc_info=True)
        return [], {}

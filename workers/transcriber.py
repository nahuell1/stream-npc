import asyncio, logging
from faster_whisper import WhisperModel
from app.memory import add_to_memory
from app.services.generator import generator  # tu wrapper (Ollama/OpenAI)

log = logging.getLogger(__name__)
model = WhisperModel("base")  # load once

async def transcribe_worker(queue: asyncio.Queue, ws_manager):
    buffer = b""
    window_ms = 5_000          # genera pregunta cada 5 s

    last_emit = asyncio.get_event_loop().time()

    while True:
        chunk = await queue.get()
        buffer += chunk
        now = asyncio.get_event_loop().time()

        # 1 · Cuando pasaron ≥5 s de audio acumulado
        if (now - last_emit) * 1000 >= window_ms:
            last_emit = now
            # Transcribe en hilo aparte para no bloquear
            text = await asyncio.to_thread(transcribe_wav_bytes, buffer)
            buffer = b""

            if text.strip():
                add_to_memory(text)
                question = await asyncio.to_thread(
                    generator.generate_question, add_to_memory.get_recent_context()
                )
                await ws_manager.broadcast(question)

def transcribe_wav_bytes(wav_bytes: bytes) -> str:
    segments, _ = model.transcribe(wav_bytes, language="es", vad_filter=True)
    return " ".join(seg.text for seg in segments)

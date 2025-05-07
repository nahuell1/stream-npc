from fastapi import FastAPI, UploadFile
import shutil
import uuid
from dotenv import load_dotenv
import os

from app.transcriber import transcribe_audio
from app.memory import add_to_memory, get_recent_context
from app.generators.ollama_generator import OllamaGenerator
from app.generators.openai_generator import OpenAIGenerator

load_dotenv()

app = FastAPI()

def get_generator():
    provider = os.getenv("AI_PROVIDER", "ollama").lower()
    if provider == "ollama":
        return OllamaGenerator()
    elif provider == "openai":
        return OpenAIGenerator()
    else:
        raise ValueError(f"Proveedor de IA no reconocido: {provider}")


generator = get_generator()

@app.post("/process-audio/")
async def process_audio(file: UploadFile):
    tmp_path = f"/tmp/{uuid.uuid4()}.wav"
    with open(tmp_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    text = transcribe_audio(tmp_path)
    add_to_memory(text)
    context = get_recent_context()
    question = generator.generate_question(context)

    return {
        "trigger": text,
        "context": context,
        "question": question
    }

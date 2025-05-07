import whisper

model = whisper.load_model("base")

def transcribe_audio(path: str) -> str:
    result = model.transcribe(path, language="es")
    return result['text']

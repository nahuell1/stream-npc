from openai import OpenAI
from .base import BaseGenerator
import os

class OpenAIGenerator(BaseGenerator):
    def __init__(self):
        self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

    def generate_question(self, context: str) -> str:
        prompt = f"""
Actuá como un compañero curioso. A partir de este texto reciente del streamer, hacé una pregunta interesante, graciosa o profunda:

\"{context.strip()}\"

Pregunta:
"""
        response = self.client.chat.completions.create(
            model="gpt-4",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.8
        )
        return response.choices[0].message.content.strip()

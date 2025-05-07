from openai import OpenAI
from .base import BaseGenerator
import os

class OpenAIGenerator(BaseGenerator):
    """Question generator using OpenAI's language models.
    
    This generator uses OpenAI's API to generate questions based on stream context,
    simulating a curious viewer's perspective.
    """
    def __init__(self):
        self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

    def generate_question(self, context: str) -> str:
        """Generate a question based on the stream context.
        
        Args:
            context: The recent stream context to generate a question from.
            
        Returns:
            A generated question as a string.
        """
        prompt = f"""
Act as a curious companion. Based on this recent text from the streamer, ask an interesting, funny, or deep question:

\"{context.strip()}\"

Question:
"""
        response = self.client.chat.completions.create(
            model="gpt-4",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.8
        )
        return response.choices[0].message.content.strip()

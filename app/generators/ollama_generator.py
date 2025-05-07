from ollama import Client
from .base import BaseGenerator
from .prompts import get_prompt_for_category
import os

class OllamaGenerator(BaseGenerator):
    """Question generator using Ollama's language models.
    
    This generator uses Ollama's API to generate questions based on stream context,
    simulating a curious Twitch viewer's perspective.
    """
    def __init__(self):
        host = os.getenv("OLLAMA_HOST", "http://localhost:11434")
        self.model = os.getenv("OLLAMA_MODEL", "llama3")
        self.client = Client(host=host)
        self.current_category = os.getenv("TWITCH_CATEGORY", "Just Chatting")

    def set_category(self, category: str):
        """Update the current Twitch category.
        
        Args:
            category: The new Twitch category name
        """
        self.current_category = category

    def generate_question(self, context: str) -> str:
        """Generate a question based on the stream context.
        
        Args:
            context: The recent stream context to generate a question from.
            
        Returns:
            A generated question as a string.
        """
        prompt_template = get_prompt_for_category(self.current_category)
        prompt = prompt_template.format(context=context)
        
        response = self.client.generate(model=self.model, prompt=prompt)
        return response['response'].strip()

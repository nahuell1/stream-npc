from collections import deque

memory_buffer = deque(maxlen=5)

def add_to_memory(text: str):
    memory_buffer.append(text)

def get_recent_context() -> str:
    return " ".join(memory_buffer)

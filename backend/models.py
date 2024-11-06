# backend/models.py

from pydantic import BaseModel
from typing import List, Dict, Any

class Message(BaseModel):
    content: str          # User's message content
    model: str            # Model name to use
    history: List[Dict[str, Any]]   # List of past messages
    chat_id: int          # Unique identifier for the chat

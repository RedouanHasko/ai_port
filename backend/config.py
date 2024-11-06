# backend/config.py

import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# API Configuration
OLLAMA_API_BASE_URL = os.getenv("OLLAMA_API_BASE_URL", "http://localhost:11434/api")
GOOGLE_API_KEY = os.getenv("GOOGLE_CUSTOM_SEARCH_API_KEY")
SEARCH_ENGINE_ID = os.getenv("GOOGLE_CUSTOM_SEARCH_ENGINE_ID")

# Memory Configuration
MEMORY_FILE = os.getenv("MEMORY_FILE", "memory.json")
MAX_MEMORY_FILE_SIZE = 4 * 1024 * 1024 * 1024  # 4GB

# FastAPI Configuration
ALLOWED_ORIGINS = os.getenv("ALLOWED_ORIGINS", "http://localhost:5173").split(",")

# Model Preferences
DEFAULT_MODEL = os.getenv("DEFAULT_MODEL", "Llama3.2:3B")

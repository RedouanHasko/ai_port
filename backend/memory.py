# backend/memory.py

import os
import json
import logging
import re
from typing import Dict, Any, Tuple

from config import MEMORY_FILE, MAX_MEMORY_FILE_SIZE

# Configure logging
logger = logging.getLogger(__name__)

def load_memory() -> Dict[str, Any]:
    """
    Loads the memory from the MEMORY_FILE.
    Initializes an empty memory if file doesn't exist or is corrupted.
    """
    if os.path.exists(MEMORY_FILE):
        try:
            if os.path.getsize(MEMORY_FILE) > MAX_MEMORY_FILE_SIZE:
                logger.error("Memory file exceeds maximum allowed size. Initializing empty memory.")
                return {"memory_store": {}, "chats": {}}
            with open(MEMORY_FILE, "r") as f:
                memory = json.load(f)
            logger.info("Memory loaded successfully.")
            if "memory_store" not in memory:
                memory["memory_store"] = {}
            if "chats" not in memory:
                memory["chats"] = {}
            return memory
        except json.JSONDecodeError:
            logger.error("Memory file is corrupted. Initializing empty memory.")
        except Exception as e:
            logger.error(f"Unexpected error loading memory: {e}")
    return {"memory_store": {}, "chats": {}}

def save_memory(memory: Dict[str, Any]):
    """
    Saves the memory to the MEMORY_FILE.
    """
    try:
        with open(MEMORY_FILE, "w") as f:
            json.dump(memory, f, indent=4)
        logger.info("Memory saved successfully.")
    except Exception as e:
        logger.error(f"Failed to save memory: {e}")

def update_conversation_history(memory: dict, chat_id: str, role: str, content: str):
    """
    Updates the conversation history in memory.
    """
    if "chats" not in memory:
        memory["chats"] = {}
    if chat_id not in memory["chats"]:
        memory["chats"][chat_id] = {"conversation_history": [], "memory_store": {}}
    if "conversation_history" not in memory["chats"][chat_id]:
        memory["chats"][chat_id]["conversation_history"] = []
    memory["chats"][chat_id]["conversation_history"].append({"role": role, "content": content})

def store_memory(chat_memory: dict, extracted_info: Dict[str, str]):
    """
    Stores extracted information into the memory_store within a specific chat.
    Prevents duplicates by checking existing entries.
    """
    for key, value in extracted_info.items():
        if key not in chat_memory["memory_store"]:
            chat_memory["memory_store"][key] = value
            logger.info(f"Stored new memory - {key}: {value}")
        else:
            if chat_memory["memory_store"][key] != value:
                logger.info(f"Updating memory - {key}: {value}")
                chat_memory["memory_store"][key] = value
            else:
                logger.debug(f"Memory '{key}' already up-to-date. Skipping duplicate.")

def extract_memory_from_message(message: Dict[str, Any]) -> Tuple[Dict[str, str], bool]:
    """
    Extracts memory-related information from the user's message.
    Returns a tuple of (memory_dict, is_change_request).
    """
    user_name = None
    is_change_request = False
    text = message['content'].lower()

    # Extract user name
    name_match = re.search(r"my name is ([a-zA-Z\s]+)", text)
    if name_match:
        user_name = name_match.group(1).strip().title()

    # Detect change requests
    if "change my name" in text or "update my name" in text:
        is_change_request = True

    memory = {}
    if user_name:
        memory["user_name"] = user_name

    return memory, is_change_request

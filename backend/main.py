# backend/main.py

import os
import re
import json
import asyncio
import logging
from typing import List, Dict, Any, Tuple

import httpx
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from config import ALLOWED_ORIGINS, DEFAULT_MODEL, OLLAMA_API_BASE_URL  # Ensure correct import
from memory import (
    load_memory,
    save_memory,
    update_conversation_history,
    extract_memory_from_message,
    store_memory
)
from search import search_and_summarize
from model_management import start_model
from utils import get_logger

# Initialize Logger
logger = get_logger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="Ollama-React Integration",
    description="Backend service to connect Ollama LLMs with a React frontend.",
    version="1.0.0"
)

# CORS middleware configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,  # e.g., ["http://localhost:5173"]
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ----------------------------
# Pydantic Models
# ----------------------------

class Message(BaseModel):
    content: str          # User's message content
    model: str            # Model name to use
    history: List[Dict[str, Any]]   # List of past messages
    chat_id: int          # Unique identifier for the chat

# ----------------------------
# Helper Functions
# ----------------------------

def construct_prompt(conversation_history: List[Dict[str, Any]], memory_store: Dict[str, Any], user_message: str) -> str:
    """
    Constructs the prompt to send to the LLM based on conversation history, memory store, and the latest user message.
    """
    prompt = (
        "You are Hasko, a friendly and intelligent assistant. "
        "Provide clear and concise answers. Only include code snippets when the user explicitly requests them. "
        "When providing code, present it within triple backticks with the appropriate language specified.\n\n"
    )
    
    # Include user-specific information from memory_store
    if "user_name" in memory_store:
        prompt += f"User's Name: {memory_store['user_name']}\n"
    
    for message in conversation_history:
        role = "User" if message["role"] == "user" else "Hasko"
        prompt += f"{role}: {message['content']}\n"
    
    # Explicit instruction to avoid unnecessary code
    prompt += (
        "Please ensure that your responses do not contain code unless explicitly requested by the user.\n"
        "Respond appropriately to the user's messages based on their content.\n\n"
    )
    
    prompt += f"User: {user_message}\nHasko:"
    return prompt

# ----------------------------
# API Endpoints
# ----------------------------

@app.post("/send-message")
async def send_message(msg: Message):
    """
    Endpoint to handle user messages. It processes the message, determines if a search is needed,
    performs the search and summarization if required, and returns the assistant's response.
    """
    model_name = msg.model if msg.model else DEFAULT_MODEL

    logger.info(f"Received message: '{msg.content}' | Model: '{model_name}' | Chat ID: {msg.chat_id}")

    # Start the model if not running
    if not start_model(model_name):
        logger.error(f"Failed to start or connect to model '{model_name}'")
        raise HTTPException(status_code=500, detail=f"Failed to start or connect to model '{model_name}'")

    # Load existing memory
    memory = load_memory()
    chat_id_str = str(msg.chat_id)

    # Initialize chat if it doesn't exist
    if "chats" not in memory:
        memory["chats"] = {}
    
    if chat_id_str not in memory["chats"]:
        memory["chats"][chat_id_str] = {"conversation_history": [], "memory_store": {}}
    
    chat_history = memory["chats"][chat_id_str]["conversation_history"]
    memory_store = memory["chats"][chat_id_str].get("memory_store", {})

    # Extract new memory from user message
    new_memory, is_change_request = extract_memory_from_message({'content': msg.content, 'isUser': True})

    # Handle change requests (e.g., updating user information)
    if is_change_request:
        memory["chats"][chat_id_str]["memory_store"].update(new_memory)
        response_message = "Are you sure you want to update this information? Please reply with 'Yes' or 'No'."
        update_conversation_history(memory, chat_id_str, "hasko", response_message)
        save_memory(memory)
        return StreamingResponse(iter([response_message]), media_type="text/plain")

    # Update memory with new information if any
    if new_memory:
        store_memory(memory["chats"][chat_id_str], new_memory)
        user_name = memory["chats"][chat_id_str]["memory_store"].get("user_name", "there")
        response_greeting = f"Got it, {user_name}!"
        update_conversation_history(memory, chat_id_str, "hasko", response_greeting)
        save_memory(memory)

    # Special handling for "what is my name" question
    if re.search(r'\bwhat is my name\b', msg.content.lower()):
        if "user_name" in memory_store:
            response_message = f"Your name is {memory_store['user_name']}."
            update_conversation_history(memory, chat_id_str, "hasko", response_message)
            save_memory(memory)
            return StreamingResponse(iter([response_message]), media_type="text/plain")
        else:
            response_message = "I don't know your name yet. Could you please tell me your name?"
            update_conversation_history(memory, chat_id_str, "hasko", response_message)
            save_memory(memory)
            return StreamingResponse(iter([response_message]), media_type="text/plain")

    # Define search keywords with broader coverage
    search_keywords = [
        "search the internet for", "search the web for", "find", "look up",
        "tell me about", "who is", "what is", "current weather in",
        "today's weather in", "weather today in", "weather forecast for",
        "latest news on", "news about", "information on", "details about"
    ]

    # Check if the message requires an internet search
    if any(keyword in msg.content.lower() for keyword in search_keywords):
        # Extract the search query using regex
        query = re.search(
            r"(search the internet for|search the web for|find|look up|tell me about|who is|what is|current weather in|today's weather in|weather today in|weather forecast for|latest news on|news about|information on|details about) (.+)",
            msg.content.lower()
        )
        if query:
            search_query = query.group(2).strip()
            logger.info(f"Performing search for query: '{search_query}'")
            web_content = await search_and_summarize(search_query, model_name)
            logger.info(f"Search and summarization completed. Response: '{web_content}'")
            # Only wrap in code block if web_content contains code
            if re.search(r'```(\w+)?\n([\s\S]*?)```', web_content):
                response_message = f"Here's what I found:\n\n{web_content}"
            else:
                response_message = f"Here's what I found:\n\n{web_content}"
            update_conversation_history(memory, chat_id_str, "hasko", response_message)
            save_memory(memory)
            return StreamingResponse(iter([response_message]), media_type="text/plain")
        else:
            logger.warning(f"Unable to extract search query from message: '{msg.content}'")

    # If no search is required, proceed to construct prompt and get response from LLM
    prompt = construct_prompt(chat_history, memory_store, msg.content)
    logger.info(f"Constructed prompt for LLM: '{prompt}'")

    # Add user message to memory
    update_conversation_history(memory, chat_id_str, "user", msg.content)
    save_memory(memory)

    # Stream response from LLM
    async def stream_response():
        try:
            async with httpx.AsyncClient(timeout=None) as client:
                async with client.stream(
                    "POST",
                    f"{OLLAMA_API_BASE_URL}/generate",
                    json={"model": model_name, "prompt": prompt, "stream": True},
                ) as response:
                    response.raise_for_status()
                    llm_response = ""
                    async for line in response.aiter_lines():
                        if line:
                            try:
                                data = json.loads(line)
                                chunk = data.get("response", "")
                                if chunk:
                                    llm_response += chunk
                                    logger.debug(f"Received chunk from LLM: '{chunk}'")
                                    yield chunk
                                    await asyncio.sleep(0)
                            except json.JSONDecodeError:
                                logger.error(f"Failed to decode JSON line: '{line}'")
            # After streaming, ensure the entire response is captured
            logger.debug(f"Full LLM Response: '{llm_response}'")
        except httpx.HTTPError as http_err:
            logger.error(f"HTTP error during LLM communication: {http_err}")
            yield "I encountered an error while processing your request."
        except Exception as e:
            logger.error(f"Unexpected error during LLM communication: {e}")
            yield "An unexpected error occurred while processing your request."

    return StreamingResponse(stream_response(), media_type="text/plain")

# ----------------------------
# Models Endpoint
# ----------------------------

@app.get("/models")
async def list_models():
    """
    Retrieves the list of available models from the Ollama API.
    """
    try:
        logger.info(f"Fetching models from Ollama API at '{OLLAMA_API_BASE_URL}/tags'")
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{OLLAMA_API_BASE_URL}/tags")
            response.raise_for_status()
        models_data = response.json().get("models", [])
        model_names = [model["name"] for model in models_data]
        logger.info(f"Retrieved models: {model_names}")
        return {"models": model_names}
    except httpx.HTTPError as http_err:
        logger.error(f"HTTP error while fetching models: {http_err}")
        raise HTTPException(status_code=500, detail="Failed to retrieve models from Ollama API.")
    except Exception as e:
        logger.error(f"Unexpected error while fetching models: {e}")
        raise HTTPException(status_code=500, detail="An unexpected error occurred while retrieving models.")

# ----------------------------
# Root Endpoint
# ----------------------------

@app.get("/")
async def root():
    return {"message": "Ollama-React Integration Backend is running."}

# ----------------------------
# Run the application
# ----------------------------

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)

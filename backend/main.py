from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
import httpx
import subprocess
import time
import traceback
import json
import asyncio
import os
import requests
import re
from dotenv import load_dotenv  # Import load_dotenv to read .env files

# Load environment variables from .env file
load_dotenv()

app = FastAPI()

# CORS middleware to allow communication with frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # Adjust as needed
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Data model for incoming messages
class Message(BaseModel):
    content: str
    model: str
    history: list  # Full conversation history
    chat_id: int  # Chat identifier

# Constants
OLLAMA_API_BASE_URL = "http://localhost:11434/api"
MAX_MEMORY_FILE_SIZE = 4 * 1024 * 1024 * 1024  # 4GB in bytes
MEMORY_FILE = "memory.json"  # Single memory file

# Retrieve API key and Search Engine ID from environment variables
GOOGLE_API_KEY = os.getenv("GOOGLE_CUSTOM_SEARCH_API_KEY")
SEARCH_ENGINE_ID = os.getenv("GOOGLE_CUSTOM_SEARCH_ENGINE_ID")

def is_model_running(model_name: str) -> bool:
    try:
        result = subprocess.run(
            ["ollama", "ps"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        return model_name in result.stdout
    except Exception as e:
        print("Error checking model status:", str(e))
        return False

def start_model(model_name: str) -> bool:
    if not is_model_running(model_name):
        try:
            subprocess.Popen(
                ["ollama", "run", model_name],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            time.sleep(3)  # Allow some time for the model to start
            return True
        except Exception as e:
            print(f"Failed to start model {model_name}: {e}")
            return False
    return True

def load_memory():
    if os.path.exists(MEMORY_FILE):
        if os.path.getsize(MEMORY_FILE) > MAX_MEMORY_FILE_SIZE:
            # Handle the case when the memory file exceeds the size limit
            print(f"Memory file {MEMORY_FILE} exceeds 4GB. Truncating the file.")
            truncate_memory_file()
        with open(MEMORY_FILE, "r") as f:
            memory = json.load(f)
    else:
        memory = {}
    return memory

def save_memory(memory: dict):
    with open(MEMORY_FILE, "w") as f:
        json.dump(memory, f)
    if os.path.getsize(MEMORY_FILE) > MAX_MEMORY_FILE_SIZE:
        # Handle the case when the memory file exceeds the size limit after saving
        print(f"Memory file {MEMORY_FILE} exceeds 4GB after saving. Truncating the file.")
        truncate_memory_file()

def truncate_memory_file():
    # Implement a strategy to reduce the memory file size
    with open(MEMORY_FILE, "r") as f:
        memory = json.load(f)
    # Example strategy: Remove oldest entries based on chat_id
    sorted_chat_ids = sorted(memory.keys())
    while os.path.getsize(MEMORY_FILE) > MAX_MEMORY_FILE_SIZE and sorted_chat_ids:
        oldest_chat_id = sorted_chat_ids.pop(0)
        del memory[oldest_chat_id]
        with open(MEMORY_FILE, "w") as f:
            json.dump(memory, f)

def extract_memory_from_message(message):
    user_name = None
    favorite_color = None
    text = message['text'].lower()
    is_change_request = False

    # Extract information
    if "my name is" in text:
        parts = text.split("my name is")
        if len(parts) > 1:
            name_part = parts[1].strip().split()[0]
            user_name = name_part.capitalize()
    if "my favorite color is" in text:
        parts = text.split("my favorite color is")
        if len(parts) > 1:
            color_part = parts[1].strip().split()[0]
            favorite_color = color_part.capitalize()

    # Detect change requests
    if "change my name to" in text or "update my name to" in text:
        parts = re.split("change my name to|update my name to", text)
        if len(parts) > 1:
            name_part = parts[1].strip().split()[0]
            user_name = name_part.capitalize()
            is_change_request = True

    if "change my favorite color to" in text or "update my favorite color to" in text:
        parts = re.split("change my favorite color to|update my favorite color to", text)
        if len(parts) > 1:
            color_part = parts[1].strip().split()[0]
            favorite_color = color_part.capitalize()
            is_change_request = True

    memory = {}
    if user_name:
        memory["user_name"] = user_name
    if favorite_color:
        memory["favorite_color"] = favorite_color
    return memory, is_change_request

def extract_query_from_message(message_text):
    # Extracts the query from the user's message
    patterns = [
        r"tell me about (.+)",
        r"search for (.+)",
        r"look up (.+)",
        r"who is (.+)",
        r"what is (.+)",
        r"latest (.+)",
    ]
    for pattern in patterns:
        match = re.search(pattern, message_text, re.IGNORECASE)
        if match:
            return match.group(1).strip()
    return None

def search_web(query):
    try:
        api_key = GOOGLE_API_KEY
        search_engine_id = SEARCH_ENGINE_ID
        if not api_key:
            print("Error: Google Custom Search API key is not set or invalid.")
            return ""
        if not search_engine_id:
            print("Error: Google Custom Search Engine ID is not set or invalid.")
            return ""
        search_url = "https://www.googleapis.com/customsearch/v1"
        params = {
            "key": api_key,
            "cx": search_engine_id,
            "q": query,
        }
        response = requests.get(search_url, params=params)
        response.raise_for_status()
        search_results = response.json()

        # Extract snippets from the search results
        snippets = []
        for item in search_results.get('items', []):
            snippets.append(item.get('snippet', ''))

        # Combine snippets
        combined_snippets = '\n'.join(snippets)

        # Limit the amount of content to avoid exceeding prompt size limits
        max_length = 1500  # Adjust as needed
        return combined_snippets[:max_length]
    except requests.exceptions.HTTPError as http_err:
        print(f"HTTP error occurred during web search: {http_err}")
        return ""
    except Exception as e:
        print(f"An unexpected error occurred during web search: {e}")
        return ""

@app.post("/send-message")
async def send_message(msg: Message):
    print(f"Received user message: {msg.content}")

    if not start_model(msg.model):
        raise HTTPException(status_code=500, detail=f"Failed to start or connect to model {msg.model}")

    # Load existing memory
    memory = load_memory()
    chat_memory = memory.get(str(msg.chat_id), {})  # Memory specific to the chat

    # Extract new memory from the latest user message
    new_memory, is_change_request = extract_memory_from_message({'text': msg.content, 'isUser': True})

    # Check if it's a change request that requires confirmation
    if is_change_request:
        # Store the change request in the chat memory for confirmation
        chat_memory['pending_change'] = new_memory
    else:
        # Update the chat memory with new information
        chat_memory.update(new_memory)
        if 'pending_change' in chat_memory:
            del chat_memory['pending_change']  # Clear any pending changes

    # Update the main memory
    memory[str(msg.chat_id)] = chat_memory
    save_memory(memory)

    # Check if there's a pending change that needs confirmation
    pending_change = chat_memory.get('pending_change', {})

    # Check if the user is requesting web content
    web_content = ""
    user_message_lower = msg.content.lower()
    query = None

    if any(keyword in user_message_lower for keyword in ["visit", "scrape", "look up", "search for", "tell me about", "who is", "what is", "latest"]):
        # Extract the query from the user's message
        query = extract_query_from_message(msg.content)
        if query:
            web_content = search_web(query)
            if web_content:
                print(f"Fetched information about '{query}'")
            else:
                print(f"No web content found for query: '{query}'")
        else:
            print("No valid query found in the message.")

    # Construct the prompt from the conversation history
    prompt = ""

    # Updated System Prompt
    prompt += (
        "System: You are a smart and friendly assistant capable of accessing the internet to fetch current information when needed. "
        "You remember important information that the user tells you, such as their name, preferences, and previous conversations. "
        "Use any information fetched from the internet to provide accurate and up-to-date responses to the user's queries. "
        "When the user requests information about public figures, products, or well-known entities, you should search for and present relevant information from reliable sources. "
        "Always ensure that the information you provide is current and accurate.\n\n"
    )

    # Include web content if available
    if web_content and query:
        prompt += f"The following information has been retrieved from the internet about '{query}':\n{web_content}\n\n"
        prompt += "Please use this information to provide an accurate and up-to-date answer to the user's question.\n\n"

    # Include memory in the prompt
    if chat_memory:
        prompt += "Important information about the user:\n"
        for key, value in chat_memory.items():
            if key != 'pending_change':
                prompt += f"- {key.replace('_', ' ').capitalize()}: {value}\n"
        prompt += "\n"

    # Include pending change if any
    if pending_change:
        prompt += "The user has requested to change the following information:\n"
        for key, value in pending_change.items():
            prompt += f"- {key.replace('_', ' ').capitalize()}: {value}\n"
        prompt += "Please confirm the change with the user before updating the information.\n\n"

    # Append the conversation history
    for message in msg.history:
        role = "User" if message['isUser'] else "Assistant"
        prompt += f"{role}: {message['text']}\n"
    prompt += "Assistant:"

    # Debug: Print the constructed prompt
    print(f"Constructed prompt:\n{prompt}")

    async def stream_response():
        try:
            async with httpx.AsyncClient(timeout=None) as client:
                async with client.stream(
                    "POST",
                    f"{OLLAMA_API_BASE_URL}/generate",
                    json={"model": msg.model, "prompt": prompt, "stream": True},
                ) as response:
                    response.raise_for_status()
                    async for line in response.aiter_lines():
                        if line:
                            # Each line is a JSON string containing a "response" field
                            data = json.loads(line)
                            llm_response_chunk = data.get("response", "")
                            if llm_response_chunk:
                                print(f"Streaming chunk: {llm_response_chunk}")
                                yield llm_response_chunk
                                await asyncio.sleep(0)  # Yield control to the event loop
        except Exception as e:
            print("An unexpected error occurred during streaming:", str(e))
            traceback.print_exc()
            yield "[Error] An unexpected error occurred during streaming."

    return StreamingResponse(stream_response(), media_type="text/plain")

@app.get("/models")
async def list_models():
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{OLLAMA_API_BASE_URL}/tags")
            response.raise_for_status()
        models_data = response.json().get("models", [])
        model_names = [model["name"] for model in models_data]
        return {"models": model_names}
    except Exception as e:
        print("An error occurred while fetching models:", str(e))
        traceback.print_exc()
        raise HTTPException(status_code=500, detail="Failed to retrieve models")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)

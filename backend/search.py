# backend/search.py

import json
import logging
import httpx
import asyncio
from typing import Optional

from config import GOOGLE_API_KEY, SEARCH_ENGINE_ID, OLLAMA_API_BASE_URL
from utils import get_logger

logger = get_logger(__name__)

async def search_and_summarize(query: str, model_name: str) -> str:
    """
    Performs a Google Custom Search for the given query and summarizes the results using the LLM.
    Returns the summarized information.
    """
    logger.info(f"Starting search for query: '{query}' using model: '{model_name}'")
    try:
        # Perform Google Custom Search
        search_url = "https://www.googleapis.com/customsearch/v1"
        params = {
            "key": GOOGLE_API_KEY,
            "cx": SEARCH_ENGINE_ID,
            "q": query,
        }
        async with httpx.AsyncClient() as client:
            response = await client.get(search_url, params=params)
            response.raise_for_status()
            search_results = response.json()

        if "items" not in search_results:
            logger.warning("No search results found.")
            return "I couldn't find any information related to your query."

        # Extract snippets from search results
        snippets = [item.get('snippet', '') for item in search_results.get('items', [])]
        combined_snippets = ' '.join(snippets)
        max_length = 1000  # Limit length to avoid overwhelming the LLM
        combined_snippets = combined_snippets[:max_length]

        logger.debug(f"Combined snippets for summarization: '{combined_snippets}'")

        # Prepare the prompt for summarization
        summary_prompt = (
            f"You are Hasko, a helpful AI assistant. Summarize the following information in a clear and concise way:\n{combined_snippets}\n\nSummary:"
        )

        # Send the summarization request to Ollama's LLM
        async with httpx.AsyncClient(timeout=None) as client:
            async with client.stream(
                "POST",
                f"{OLLAMA_API_BASE_URL}/generate",
                json={"model": model_name, "prompt": summary_prompt, "stream": True},
            ) as response:
                response.raise_for_status()
                summary = ""
                async for line in response.aiter_lines():
                    if line:
                        try:
                            data = json.loads(line)
                            chunk = data.get("response", "")
                            if chunk:
                                logger.debug(f"Received chunk from LLM: '{chunk}'")
                                summary += chunk
                                await asyncio.sleep(0)
                        except json.JSONDecodeError:
                            logger.error(f"Failed to decode JSON line: '{line}'")
                logger.info(f"Summarization completed. Summary: '{summary.strip()}'")
                return summary.strip()

    except httpx.HTTPError as http_err:
        logger.error(f"HTTP error during web search: {http_err}")
        return "I couldn't retrieve information from the internet right now."
    except Exception as e:
        logger.error(f"Unexpected error during web search: {e}")
        return "An error occurred while retrieving information."

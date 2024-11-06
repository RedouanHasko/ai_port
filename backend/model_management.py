# backend/model_management.py

import subprocess
import time
import logging

from utils import get_logger

logger = get_logger(__name__)

def is_model_running(model_name: str) -> bool:
    """
    Checks if the specified model is currently running.
    """
    try:
        result = subprocess.run(
            ["ollama", "ps"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        logger.debug(f"Ollama 'ps' output: {result.stdout}")
        return model_name in result.stdout
    except Exception as e:
        logger.error(f"Error checking model status: {e}")
        return False

def start_model(model_name: str) -> bool:
    """
    Starts the specified model if it's not already running.
    """
    if not is_model_running(model_name):
        try:
            logger.info(f"Attempting to start model '{model_name}'")
            subprocess.Popen(
                ["ollama", "run", model_name],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            logger.info(f"Starting model '{model_name}'...")
            time.sleep(5)  # Wait for the model to initialize
            if is_model_running(model_name):
                logger.info(f"Model '{model_name}' started successfully.")
                return True
            else:
                logger.error(f"Model '{model_name}' failed to start.")
                return False
        except Exception as e:
            logger.error(f"Failed to start model '{model_name}': {e}")
            return False
    else:
        logger.info(f"Model '{model_name}' is already running.")
        return True

# Ollama-React Integration Backend

## Overview

This backend application serves as a bridge between the Ollama Local Language Models (LLMs) and a React frontend UI. It allows users to select from locally installed LLMs, engage in chat interactions, perform internet searches, and maintains conversation memory across sessions.

## Features

- **Model Management**: Lists available LLMs and ensures the selected model is running.
- **Chat Interface**: Facilitates real-time chat between the user and the selected LLM.
- **Internet Search**: Integrates Google Custom Search API to fetch and summarize web content.
- **Memory Persistence**: Stores important conversation data in `memory.json` to retain context across sessions and restarts.
- **Modular Codebase**: Organized into multiple Python modules for better maintainability and scalability.

## Prerequisites

- **Python 3.8+**
- **Ollama Installed Locally**
- **Google Custom Search API Key and Search Engine ID**

## Installation

1. **Clone the Repository**

   ```bash
   git clone https://github.com/RedouanHasko/ai_port.git
   cd ai_port/backend
   ```

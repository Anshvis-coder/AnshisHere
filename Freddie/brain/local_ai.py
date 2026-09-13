"""
Local AI Module for Freddie
============================
Interfaces with Ollama for local LLM inference.
No API keys required - runs completely offline.
"""

import logging
import requests
from typing import Optional
from config import OLLAMA_BASE_URL, OLLAMA_MODEL, OLLAMA_TIMEOUT

logger = logging.getLogger(__name__)


class LocalAI:
    """Handles communication with local Ollama service."""

    def __init__(self, base_url: str = None, model: str = None):
        self.base_url = base_url or OLLAMA_BASE_URL
        self.model = model or OLLAMA_MODEL
        self.timeout = OLLAMA_TIMEOUT
        self._available: Optional[bool] = None

    def is_available(self) -> bool:
        """Check if Ollama service is running and accessible."""
        if self._available is not None:
            return self._available

        try:
            response = requests.get(f"{self.base_url}/api/tags", timeout=5)
            if response.status_code == 200:
                self._available = True
                logger.info("Ollama service is available")
                return True
            else:
                self._available = False
                logger.warning(f"Ollama returned status code: {response.status_code}")
                return False
        except requests.exceptions.ConnectionError:
            self._available = False
            logger.warning("Cannot connect to Ollama service. Is it running?")
            return False
        except requests.exceptions.Timeout:
            self._available = False
            logger.warning("Connection to Ollama timed out")
            return False
        except Exception as e:
            self._available = False
            logger.error(f"Error checking Ollama availability: {e}")
            return False

    def get_available_models(self) -> list:
        """Get list of available models from Ollama."""
        try:
            response = requests.get(f"{self.base_url}/api/tags", timeout=self.timeout)
            if response.status_code == 200:
                data = response.json()
                models = [model.get("name", "") for model in data.get("models", [])]
                logger.info(f"Available models: {models}")
                return models
            else:
                logger.warning(f"Failed to get models: {response.status_code}")
                return []
        except Exception as e:
            logger.error(f"Error getting models: {e}")
            return []

    def generate_response(self, prompt: str, stream: bool = False) -> str:
        """
        Generate a response from the local AI model.

        Args:
            prompt: The user's input/prompt
            stream: Whether to stream the response (default: False)

        Returns:
            The AI's response text
        """
        if not self.is_available():
            raise ConnectionError("Ollama service is not available")

        url = f"{self.base_url}/api/generate"
        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": stream,
            "options": {
                "temperature": 0.7,
                "top_p": 0.9,
            }
        }

        try:
            logger.debug(f"Sending prompt to Ollama: {prompt[:100]}...")
            response = requests.post(url, json=payload, timeout=self.timeout)
            response.raise_for_status()

            if stream:
                # Handle streaming response
                return self._handle_stream_response(response)
            else:
                # Handle non-streaming response
                data = response.json()
                result = data.get("response", "")
                logger.debug(f"Received response: {result[:100]}...")
                return result.strip()

        except requests.exceptions.Timeout:
            logger.error("Request to Ollama timed out")
            raise TimeoutError("AI request timed out. The model may be too large or busy.")
        except requests.exceptions.RequestException as e:
            logger.error(f"Request error: {e}")
            raise ConnectionError(f"Failed to communicate with Ollama: {str(e)}")
        except Exception as e:
            logger.error(f"Unexpected error generating response: {e}")
            raise RuntimeError(f"AI generation failed: {str(e)}")

    def _handle_stream_response(self, response: requests.Response) -> str:
        """Handle streaming response from Ollama."""
        full_response = ""
        for line in response.iter_lines():
            if line:
                try:
                    data = line.decode('utf-8')
                    import json
                    json_data = json.loads(data)
                    chunk = json_data.get("response", "")
                    full_response += chunk
                except:
                    continue
        return full_response.strip()

    def chat(self, messages: list, stream: bool = False) -> str:
        """
        Send a chat conversation to the model.

        Args:
            messages: List of message dicts with 'role' and 'content'
            stream: Whether to stream the response

        Returns:
            The AI's response text
        """
        if not self.is_available():
            raise ConnectionError("Ollama service is not available")

        url = f"{self.base_url}/api/chat"
        payload = {
            "model": self.model,
            "messages": messages,
            "stream": stream,
        }

        try:
            logger.debug(f"Sending chat messages to Ollama")
            response = requests.post(url, json=payload, timeout=self.timeout)
            response.raise_for_status()

            if stream:
                return self._handle_stream_response(response)
            else:
                data = response.json()
                message = data.get("message", {})
                result = message.get("content", "")
                return result.strip()

        except Exception as e:
            logger.error(f"Chat error: {e}")
            raise RuntimeError(f"Chat failed: {str(e)}")

    def set_model(self, model_name: str) -> bool:
        """
        Change the active model.

        Args:
            model_name: Name of the model to use

        Returns:
            True if successful, False otherwise
        """
        try:
            # Verify model exists
            available = self.get_available_models()
            if model_name in available or model_name.startswith(model_name):
                self.model = model_name
                logger.info(f"Model changed to: {model_name}")
                return True
            else:
                logger.warning(f"Model '{model_name}' not found in available models")
                return False
        except Exception as e:
            logger.error(f"Error setting model: {e}")
            return False

    def get_current_model(self) -> str:
        """Get the current model name."""
        return self.model

    def pull_model(self, model_name: str) -> bool:
        """
        Pull/download a model from Ollama library.

        Args:
            model_name: Name of the model to pull

        Returns:
            True if successful, False otherwise
        """
        url = f"{self.base_url}/api/pull"
        payload = {"name": model_name}

        try:
            logger.info(f"Pulling model: {model_name}")
            response = requests.post(url, json=payload, timeout=300)
            if response.status_code == 200:
                logger.info(f"Model '{model_name}' pulled successfully")
                return True
            else:
                logger.error(f"Failed to pull model: {response.status_code}")
                return False
        except Exception as e:
            logger.error(f"Error pulling model: {e}")
            return False


# Singleton instance
_ai_instance: Optional[LocalAI] = None


def get_ai() -> LocalAI:
    """Get the singleton LocalAI instance."""
    global _ai_instance
    if _ai_instance is None:
        _ai_instance = LocalAI()
    return _ai_instance

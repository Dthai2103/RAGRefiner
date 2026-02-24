import urllib.request
import urllib.error
import json
import logging
from typing import Dict, Any, Optional

from .base_llm import BaseLLM

logger = logging.getLogger(__name__)

class OllamaLLM(BaseLLM):
    """LLM implementation that communicates with a local Ollama instance via HTTP."""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.base_url = config.get("base_url", "http://localhost:11434").rstrip("/")
        self.endpoint = f"{self.base_url}/api/generate"
        self.temperature = config.get("temperature", 0.3)

    def _generate(self, prompt: str, system_prompt: Optional[str] = None, json_format: bool = False) -> str:
        """Sends a POST request to the Ollama API."""
        
        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": self.temperature
            }
        }
        
        if system_prompt:
            payload["system"] = system_prompt
            
        if json_format:
            payload["format"] = "json"
            
        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(self.endpoint, data=data, method="POST")
        req.add_header("Content-Type", "application/json")
        
        try:
            with urllib.request.urlopen(req, timeout=self.timeout) as response:
                result_json = json.loads(response.read().decode("utf-8"))
                return result_json.get("response", "")
        except urllib.error.URLError as e:
             raise Exception(f"Failed to connect to Ollama at {self.endpoint}. Is it running?: {e}")
        except Exception as e:
             raise Exception(f"Ollama generation error: {e}")

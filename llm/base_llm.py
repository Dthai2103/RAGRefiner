from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
import time
import logging

logger = logging.getLogger(__name__)

class BaseLLM(ABC):
    """Abstract base class for all LLM implementations in RAGRefiner."""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.model = config.get("model", "llama3.2")
        self.max_retries = config.get("max_retries", 3)
        self.timeout = config.get("timeout", 60)
        
    @abstractmethod
    def _generate(self, prompt: str, system_prompt: Optional[str] = None, json_format: bool = False) -> str:
        """Internal method to be implemented by subclasses."""
        pass
        
    def generate(self, prompt: str, system_prompt: Optional[str] = None, json_format: bool = False) -> str:
        """
        Generates text using the LLM with built-in retry logic.
        
        Args:
            prompt: The main user prompt.
            system_prompt: Optional system instructions.
            json_format: If true, requests the LLM to output valid JSON.
            
        Returns:
            The generated text string.
            
        Raises:
            Exception: If all retry attempts fail.
        """
        last_exception = None
        
        for attempt in range(1, self.max_retries + 1):
            try:
                # Add a small delay between retries
                if attempt > 1:
                    time.sleep(2 ** (attempt - 1)) # Exponential backoff: 2s, 4s, ...
                    
                response = self._generate(prompt, system_prompt, json_format)
                return response
                
            except Exception as e:
                last_exception = e
                logger.warning(f"LLM generation failed (Attempt {attempt}/{self.max_retries}): {e}")
                
        logger.error(f"LLM generation failed after {self.max_retries} attempts.")
        raise last_exception or Exception("Unknown LLM error")

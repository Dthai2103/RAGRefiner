from typing import Dict, Any
from .base_llm import BaseLLM
from .ollama_llm import OllamaLLM

def create_llm(config: Dict[str, Any]) -> BaseLLM:
    """Factory function to instantiate the configured LLM."""
    llm_config = config.get("llm", {})
    # Currently only supporting Ollama, but easy to extend
    return OllamaLLM(llm_config)

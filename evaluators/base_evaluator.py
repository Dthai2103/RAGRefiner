from abc import ABC, abstractmethod
from typing import Dict, Any, Tuple
import json
import logging
from llm.base_llm import BaseLLM
from models import ProcessingDocument

logger = logging.getLogger(__name__)

class BaseEvaluator(ABC):
    """Abstract base class for all AI evaluators."""
    
    def __init__(self, llm: BaseLLM):
        self.llm = llm
        
    @abstractmethod
    def get_prompt(self, text: str) -> Tuple[str, str]:
        """Returns (system_prompt, user_prompt) for the evaluation."""
        pass
        
    @abstractmethod
    def parse_response(self, response: str) -> Dict[str, Any]:
        """Parses the LLM JSON response into a dictionary of scores."""
        pass
        
    def evaluate(self, doc: ProcessingDocument) -> Dict[str, Any]:
        """Runs the LLM evaluation and returns the parsed scores."""
        system_prompt, user_prompt = self.get_prompt(doc.content)
        
        try:
            # We request JSON format from the LLM
            response_text = self.llm.generate(user_prompt, system_prompt, json_format=True)
            return self.parse_response(response_text)
        except Exception as e:
            logger.error(f"Evaluation failed for document {doc.metadata.doc_id}: {e}")
            # Return empty scores on failure; the aggregator will handle it
            return {}

    def _safe_parse_json(self, response: str) -> Dict[str, Any]:
        """Helper to safely parse potentially malformed JSON responses."""
        try:
            # Simple cleanup in case the LLM wraps it in markdown blocks
            clean_json = response.strip()
            if clean_json.startswith("```json"):
                clean_json = clean_json[7:]
            if clean_json.startswith("```"):
                clean_json = clean_json[3:]
            if clean_json.endswith("```"):
                clean_json = clean_json[:-3]
                
            return json.loads(clean_json.strip())
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON from LLM: {e}\nResponse: {response}")
            return {}

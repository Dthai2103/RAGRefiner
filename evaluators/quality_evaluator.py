import json
from typing import Dict, Any, Tuple
from .base_evaluator import BaseEvaluator

class QualityEvaluator(BaseEvaluator):
    """Evaluates the general quality of the text (coherence, language)."""
    
    def get_prompt(self, text: str) -> Tuple[str, str]:
        system_prompt = """
        You are an expert AI evaluator assessing document quality for a Retrieval-Augmented Generation (RAG) system.
        Evaluate the following text on two criteria from 0.0 to 1.0:
        1. coherence: Does the text flow logically? Are the sentences well-connected?
        2. language_quality: Is the spelling and grammar correct? Is the tone appropriate?
        
        Provide constructive feedback if the score is below 0.8.
        
        Respond ONLY with a valid JSON object matching this schema:
        {
            "coherence": float,
            "language_quality": float,
            "reasoning": "brief explanation",
            "improvement_hints": ["hint 1", "hint 2"]
        }
        """
        
        user_prompt = f"Text to evaluate:\n\n{text}"
        return system_prompt, user_prompt
        
    def parse_response(self, response: str) -> Dict[str, Any]:
        data = self._safe_parse_json(response)
        return {
            "coherence": float(data.get("coherence", 0.0)),
            "language_quality": float(data.get("language_quality", 0.0)),
            "reasoning": data.get("reasoning", ""),
            "improvement_hints": data.get("improvement_hints", [])
        }

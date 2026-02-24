from typing import Dict, Any, Tuple
from .base_evaluator import BaseEvaluator

class CompletenessEvaluator(BaseEvaluator):
    """Evaluates if the document contains complete thoughts and clear facts."""
    
    def get_prompt(self, text: str) -> Tuple[str, str]:
        system_prompt = """
        You are an expert AI evaluator assessing document completeness for a RAG system.
        Evaluate the following text on two criteria from 0.0 to 1.0:
        1. completeness: Does the text contain complete thoughts? Is it missing crucial context or cut off abruptly?
        2. factual_clarity: Are the facts and statements stated clearly without ambiguity?
        
        Provide constructive feedback if the score is below 0.8.
        
        Respond ONLY with a valid JSON object matching this schema:
        {
            "completeness": float,
            "factual_clarity": float,
            "reasoning": "brief explanation",
            "improvement_hints": ["hint 1", "hint 2"]
        }
        """
        
        user_prompt = f"Text to evaluate:\n\n{text}"
        return system_prompt, user_prompt
        
    def parse_response(self, response: str) -> Dict[str, Any]:
        data = self._safe_parse_json(response)
        return {
            "completeness": float(data.get("completeness", 0.0)),
            "factual_clarity": float(data.get("factual_clarity", 0.0)),
            "reasoning": data.get("reasoning", ""),
            "improvement_hints": data.get("improvement_hints", [])
        }

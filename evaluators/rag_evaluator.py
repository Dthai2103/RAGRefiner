from typing import Dict, Any, Tuple
from .base_evaluator import BaseEvaluator

class RAGEvaluator(BaseEvaluator):
    """Evaluates how suitable the document is for chunking and retrieval."""
    
    def get_prompt(self, text: str) -> Tuple[str, str]:
        system_prompt = """
        You are an expert AI evaluator assessing document suitability for a RAG system.
        Evaluate the following text on a single criterion from 0.0 to 1.0:
        1. rag_suitability: Is the text information-dense? Can it be easily split into meaningful chunks? Does it avoid excessive boilerplate or formatting artifacts?
        
        Provide constructive feedback if the score is below 0.8.
        
        Respond ONLY with a valid JSON object matching this schema:
        {
            "rag_suitability": float,
            "reasoning": "brief explanation",
            "improvement_hints": ["hint 1", "hint 2"]
        }
        """
        
        user_prompt = f"Text to evaluate:\n\n{text}"
        return system_prompt, user_prompt
        
    def parse_response(self, response: str) -> Dict[str, Any]:
        data = self._safe_parse_json(response)
        return {
            "rag_suitability": float(data.get("rag_suitability", 0.0)),
            "reasoning": data.get("reasoning", ""),
            "improvement_hints": data.get("improvement_hints", [])
        }

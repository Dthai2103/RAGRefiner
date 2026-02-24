import json
from typing import Dict, Any, Tuple
from .base_improver import BaseImprover
from models import ProcessingDocument
from llm.base_llm import BaseLLM
from evaluators.base_evaluator import BaseEvaluator
import logging

logger = logging.getLogger(__name__)

class MetadataEnricher(BaseImprover):
    """Uses LLM to generate keywords, summary, and topic tags for a document."""
    
    def __init__(self, llm: BaseLLM):
        self.llm = llm
        
    def _safe_parse_json(self, response: str) -> Dict[str, Any]:
         try:
             clean_json = response.strip()
             if clean_json.startswith("```json"):
                 clean_json = clean_json[7:]
             if clean_json.startswith("```"):
                 clean_json = clean_json[3:]
             if clean_json.endswith("```"):
                 clean_json = clean_json[:-3]
                 
             return json.loads(clean_json.strip())
         except json.JSONDecodeError as e:
             logger.error(f"Failed to parse metadata JSON from LLM: {e}\nResponse: {response}")
             return {}
        
    def improve(self, doc: ProcessingDocument) -> ProcessingDocument:
        system_prompt = """
        You are an expert AI document analyzer. Given a text, extract meaningful metadata for a RAG system.
        Analyze the text and provide the following:
        1. keywords: A list of 3-5 specific keywords.
        2. summary: A concise 1-sentence summary of the text.
        3. topic_tags: A list of 1-3 broad topic categories (e.g., 'AI', 'Finance', 'Engineering').
        4. language: The ISO 639-1 language code of the text (e.g., 'en', 'vi', 'es').
        
        Respond ONLY with a valid JSON object matching this schema:
        {
            "keywords": ["keyword1", "keyword2"],
            "summary": "This document describes...",
            "topic_tags": ["CategoryA", "CategoryB"],
            "language": "en"
        }
        """
        
        user_prompt = f"Text to analyze:\n\n{doc.content}"
        
        try:
             response_text = self.llm.generate(user_prompt, system_prompt, json_format=True)
             data = self._safe_parse_json(response_text)
             
             if data:
                 doc.metadata.keywords = data.get("keywords", [])
                 doc.metadata.summary = data.get("summary", "")
                 doc.metadata.topic_tags = data.get("topic_tags", [])
                 doc.metadata.language = data.get("language", "en")
                 logger.debug(f"Metadata enriched for doc {doc.metadata.doc_id}")
                 
        except Exception as e:
             logger.error(f"Metadata enrichment failed for doc {doc.metadata.doc_id}: {e}")
             
        return doc

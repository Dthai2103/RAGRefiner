import re
from typing import List
from .base_filter import BaseFilter
from models import ProcessingDocument, FilterResult

class RelevanceFilter(BaseFilter):
    """Filters out documents that do not contain allowed keywords."""
    
    def __init__(self, allowed_keywords: List[str] = None):
        self.allowed_keywords = [k.lower() for k in (allowed_keywords or [])]
        
    def filter(self, doc: ProcessingDocument) -> FilterResult:
        if not self.allowed_keywords:
            return FilterResult(True) # Pass if no keywords configured
            
        text = doc.content.lower()
        
        # Simple string contains check
        for keyword in self.allowed_keywords:
            if keyword in text:
                return FilterResult(True)
                
        # Regex check for word boundaries
        for keyword in self.allowed_keywords:
            if re.search(r'\b' + re.escape(keyword) + r'\b', text):
                return FilterResult(True)
                
        return FilterResult(False, "Document lacks relevance (no matching keywords found)")

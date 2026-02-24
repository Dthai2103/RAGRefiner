import re
from .base_improver import BaseImprover
from models import ProcessingDocument

class TextCleaner(BaseImprover):
    """Rule-based text cleaner to remove basic noise."""
    
    def improve(self, doc: ProcessingDocument) -> ProcessingDocument:
        text = doc.content
        
        # 1. Remove HTML tags
        text = re.sub(r'<[^>]+>', ' ', text)
        
        # 2. Normalize whitespace (replace multiple spaces/newlines with single ones)
        text = re.sub(r'[ \t]+', ' ', text)
        text = re.sub(r'\n\s*\n', '\n\n', text)
        
        # 3. Remove URLs (optional, depending on use case but good for reducing noise)
        text = re.sub(r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+', '', text)
        
        doc.content = text.strip()
        return doc

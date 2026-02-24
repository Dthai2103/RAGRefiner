import hashlib
from typing import Set, Dict
from .base_filter import BaseFilter
from models import ProcessingDocument, FilterResult

class DedupFilter(BaseFilter):
    """Filters out exact duplicates and near-duplicates using Jaccard similarity."""
    
    def __init__(self, jaccard_threshold: float = 0.85):
        self.jaccard_threshold = jaccard_threshold
        self.seen_hashes: Set[str] = set()
        self.seen_trigrams: Dict[str, Set[str]] = {} # doc_id -> trigram set
        
    def _get_trigrams(self, text: str) -> Set[str]:
        words = text.lower().split()
        if len(words) < 3:
            return set(words)
        return set([" ".join(words[i:i+3]) for i in range(len(words)-2)])
        
    def filter(self, doc: ProcessingDocument) -> FilterResult:
        text = doc.content.strip()
        
        # Exact match (MD5)
        md5_hash = hashlib.md5(text.encode('utf-8')).hexdigest()
        if md5_hash in self.seen_hashes:
            return FilterResult(False, "Exact duplicate found (MD5)")
            
        # Near-duplicate match (Jaccard Trigram)
        doc_trigrams = self._get_trigrams(text)
        
        for seen_id, seen_trigrams in self.seen_trigrams.items():
            if not doc_trigrams or not seen_trigrams:
                continue
                
            intersection = len(doc_trigrams.intersection(seen_trigrams))
            union = len(doc_trigrams.union(seen_trigrams))
            
            if union > 0:
                jaccard_sim = intersection / union
                if jaccard_sim >= self.jaccard_threshold:
                    return FilterResult(False, f"Near duplicate found (Jaccard sim: {jaccard_sim:.2f} with doc {seen_id})")
                    
        # If passed, store for future comparisons
        self.seen_hashes.add(md5_hash)
        self.seen_trigrams[doc.metadata.doc_id] = doc_trigrams
        
        return FilterResult(True)

import re
from .base_filter import BaseFilter
from models import ProcessingDocument, FilterResult

class QualityFilter(BaseFilter):
    """Filters out documents based on length and noise ratio."""
    
    def __init__(self, min_chars: int = 50, max_chars: int = 100000, max_noise_ratio: float = 0.35):
        self.min_chars = min_chars
        self.max_chars = max_chars
        self.max_noise_ratio = max_noise_ratio
        
    def filter(self, doc: ProcessingDocument) -> FilterResult:
        text = doc.content.strip()
        length = len(text)
        
        if length < self.min_chars:
            return FilterResult(False, f"Document too short ({length} < {self.min_chars})")
            
        if length > self.max_chars:
             return FilterResult(False, f"Document too long ({length} > {self.max_chars})")
             
        # Calculate noise ratio (non-alphanumeric vs total)
        alphanumeric = len(re.findall(r'\w', text))
        if length > 0:
            noise_ratio = 1.0 - (alphanumeric / length)
            if noise_ratio > self.max_noise_ratio:
                 return FilterResult(False, f"High noise ratio ({noise_ratio:.2f} > {self.max_noise_ratio})")
                 
        return FilterResult(True)

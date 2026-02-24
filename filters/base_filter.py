from abc import ABC, abstractmethod
from models import ProcessingDocument, FilterResult

class BaseFilter(ABC):
    """Abstract base class for all pre-filters."""
    
    @abstractmethod
    def filter(self, doc: ProcessingDocument) -> FilterResult:
        """
        Evaluates a document against the filter's rules.
        
        Args:
            doc: The document to filter.
            
        Returns:
            FilterResult indicating pass/fail and a reason.
        """
        pass

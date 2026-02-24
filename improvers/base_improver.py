from abc import ABC, abstractmethod
from typing import Dict, Any
from models import ProcessingDocument

class BaseImprover(ABC):
    """Abstract base class for document improvers (cleaners, rewriters, etc.)."""
    
    @abstractmethod
    def improve(self, doc: ProcessingDocument) -> ProcessingDocument:
        """
        Modifies the document to improve its quality or structure.
        
        Args:
            doc: The document to improve.
            
        Returns:
            The improved document (can be the same instance modified in place).
        """
        pass

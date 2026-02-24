from typing import List, Tuple
from models import ProcessingDocument, DocStatus
from .base_filter import BaseFilter
import logging

logger = logging.getLogger(__name__)

class FilterPipeline:
    """Runs a sequence of pre-filters on documents."""
    
    def __init__(self, filters: List[BaseFilter]):
        self.filters = filters
        
    def run(self, doc: ProcessingDocument) -> ProcessingDocument:
        """Runs the document through all filters."""
        for filter_instance in self.filters:
            result = filter_instance.filter(doc)
            if not result.passed:
                doc.status = DocStatus.REJECT
                doc.metadata.reject_reason = f"[{filter_instance.__class__.__name__}] {result.reason}"
                logger.info(f"Document {doc.metadata.doc_id} rejected: {doc.metadata.reject_reason}")
                return doc
                
        logger.debug(f"Document {doc.metadata.doc_id} passed all pre-filters.")
        return doc
        
    def run_batch(self, docs: List[ProcessingDocument]) -> Tuple[List[ProcessingDocument], List[ProcessingDocument]]:
        """Runs the filters on a batch of documents, returning passed and rejected lists."""
        passed = []
        rejected = []
        
        for doc in docs:
             processed_doc = self.run(doc)
             if processed_doc.status == DocStatus.REJECT:
                 rejected.append(processed_doc)
             else:
                 passed.append(processed_doc)
                 
        return passed, rejected

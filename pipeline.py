from typing import List, Dict, Any, Tuple
import time
import logging
from models import ProcessingDocument, DocumentMetadata, DocStatus
from llm import create_llm
from filters import FilterPipeline, QualityFilter, DedupFilter, RelevanceFilter
from evaluators import ScoreAggregator
from improvers import ImprovePipeline
from output import Exporter

logger = logging.getLogger(__name__)

class RAGPipeline:
    """The main orchestrator for the RAGRefiner system."""
    
    def __init__(self, config: Dict[str, Any], output_dir: str):
        self.config = config
        self.llm = create_llm(config)
        
        # 1. Filters
        self.filter_pipeline = FilterPipeline([
            QualityFilter(),
            DedupFilter(),
            RelevanceFilter() # By default, accepts all if no keywords provided
        ])
        
        # 2. Evaluators
        self.evaluator = ScoreAggregator(self.llm, config)
        
        # 3. Improvers
        self.improve_pipeline = ImprovePipeline(self.llm, config, self.evaluator)
        
        # 4. Output
        self.exporter = Exporter(output_dir)
        
    def process_document(self, content: str, doc_id: str, source: str) -> ProcessingDocument:
        """Processes a single document through the pipeline."""
        metadata = DocumentMetadata(
            doc_id=doc_id,
            source=source,
            created_at=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        )
        doc = ProcessingDocument(content=content, metadata=metadata)
        
        # Step 1: Pre-filters
        doc = self.filter_pipeline.run(doc)
        if doc.status == DocStatus.REJECT:
            return doc
            
        # Step 2: Evaluation
        doc = self.evaluator.evaluate(doc)
        
        # Step 3: Improvement & Chunking (handled as a list of 1)
        docs = self.improve_pipeline.process_and_chunk([doc])
        return docs[0] if docs else doc

    def process_batch(self, docs_input: List[Tuple[str, str, str]]) -> Dict[str, int]:
        """
        Processes a batch of documents.
        Args: docs_input: List of (content, doc_id, source) tuples
        Returns: processing statistics
        """
        logger.info(f"Starting batch processing of {len(docs_input)} documents...")
        
        all_docs = []
        for content, doc_id, source in docs_input:
             metadata = DocumentMetadata(
                 doc_id=doc_id,
                 source=source,
                 created_at=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
             )
             all_docs.append(ProcessingDocument(content=content, metadata=metadata))
             
        # Step 1: Filters
        passed_filters, rejected_filters = self.filter_pipeline.run_batch(all_docs)
        
        # Step 2: Evaluation
        for doc in passed_filters:
            self.evaluator.evaluate(doc)

        # Step 3: Improvement loop & chunking
        final_docs = self.improve_pipeline.process_and_chunk(passed_filters)
        
        # Separate passed and rejected out of final_docs
        final_passed = [d for d in final_docs if d.status == DocStatus.PASS]
        final_rejected = [d for d in final_docs if d.status == DocStatus.REJECT]
        all_rejected = rejected_filters + final_rejected
        
        # Step 4: Export
        if final_passed:
            self.exporter.export_passed(final_passed)
        if all_rejected:
            self.exporter.export_rejected(all_rejected)
            
        # Export report for all documents that reached evaluation phase
        self.exporter.export_report(passed_filters)
            
        stats = {
            "total_input": len(docs_input),
            "passed": len(final_passed),
            "rejected_filters": len(rejected_filters),
            "rejected_evaluation": len(final_rejected),
            "total_chunks_exported": sum(len(d.chunks) if hasattr(d, 'chunks') and d.chunks else 1 for d in final_passed)
        }
        
        logger.info(f"Batch complete. Stats: {stats}")
        return stats

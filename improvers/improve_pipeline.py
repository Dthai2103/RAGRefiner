from typing import Dict, Any, List
from models import ProcessingDocument, DocStatus
from llm.base_llm import BaseLLM
from evaluators.score_aggregator import ScoreAggregator
from .text_cleaner import TextCleaner
from .chunker import Chunker
from .metadata_enricher import MetadataEnricher
import logging

logger = logging.getLogger(__name__)

class ImprovePipeline:
    """Orchestrates the document improvement and chunking process."""
    
    def __init__(self, llm: BaseLLM, config: Dict[str, Any], evaluator: ScoreAggregator):
        self.config = config
        self.max_attempts = config.get("evaluation", {}).get("max_improve_attempts", 2)
        
        self.cleaner = TextCleaner()
        self.chunker = Chunker(config)
        self.enricher = MetadataEnricher(llm)
        self.evaluator = evaluator # Need this for the re-evaluate loop
        self.llm = llm # Need this for rewriting
        
    def _rewrite(self, doc: ProcessingDocument) -> None:
         """Uses LLM to rewrite document based on evaluation hints."""
         hints = doc.eval_details.improvement_hints if doc.eval_details else []
         hint_str = "\n- ".join(hints) if hints else "Improve clarity and completeness."
         
         system_prompt = f"""
         You are an expert editor refining text for a RAG system.
         Improve the given text based on this feedback from an evaluator:
         - {hint_str}
         
         Maintain the original meaning and language. DO NOT add conversational filler like 'Here is the improved version'.
         Output ONLY the improved text.
         """
         
         user_prompt = f"Original text:\n\n{doc.content}"
         
         try:
             improved_text = self.llm.generate(user_prompt, system_prompt, json_format=False)
             doc.content = improved_text.strip()
             doc.metadata.improve_attempts += 1
             logger.info(f"Doc {doc.metadata.doc_id} successfully rewritten (Attempt {doc.metadata.improve_attempts})")
         except Exception as e:
             logger.error(f"Failed to rewrite doc {doc.metadata.doc_id}: {e}")
             
    def process_and_chunk(self, docs: List[ProcessingDocument]) -> List[ProcessingDocument]:
        """Runs documents through the improve/eval loop, then enriches and chunks the passed ones."""
        final_docs = []
        
        for doc in docs:
            
            # Improvement Loop for documents marked 'IMPROVE'
            while doc.status == DocStatus.IMPROVE and doc.metadata.improve_attempts < self.max_attempts:
                 logger.info(f"Improving doc {doc.metadata.doc_id} (Attempt {doc.metadata.improve_attempts + 1}/{self.max_attempts})")
                 
                 # 1. Clean first
                 self.cleaner.improve(doc)
                 
                 # 2. Rewrite using LLM and feedback
                 self._rewrite(doc)
                 
                 # 3. Re-evaluate
                 self.evaluator.evaluate(doc)
                 
            # Final check after loops
            if doc.status == DocStatus.IMPROVE:
                 logger.warning(f"Doc {doc.metadata.doc_id} failed to pass after max attempts. Rejecting.")
                 doc.status = DocStatus.REJECT
                 doc.metadata.reject_reason = f"Failed to pass after {self.max_attempts} improvement attempts."
                 
            # If doc passed (either initially or after improvements)
            if doc.status == DocStatus.PASS:
                # 4. Enrich metadata (keywords, summary)
                self.enricher.improve(doc)
                
                # 5. Chunking
                self.chunker.improve(doc)
                
            final_docs.append(doc)
            
        return final_docs

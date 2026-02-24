import json
import os
from typing import List, Dict, Any
from models import ProcessingDocument, DocStatus
from .formatter import OutputFormatter
import logging

logger = logging.getLogger(__name__)

class Exporter:
    """Handles writing formatted documents and reports to disk."""
    
    def __init__(self, output_dir: str):
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)
        
    def export_passed(self, docs: List[ProcessingDocument]) -> None:
        """Exports passed documents and their chunks to documents.jsonl"""
        path = os.path.join(self.output_dir, "documents.jsonl")
        formatted = OutputFormatter.format_batch(docs)
        
        chunk_count = 0
        with open(path, 'a', encoding='utf-8') as f:
            for item in formatted:
                f.write(json.dumps(item, ensure_ascii=False) + "\n")
                chunk_count += 1
                
        logger.info(f"Exported {chunk_count} chunks to {path}")
        
    def export_rejected(self, docs: List[ProcessingDocument]) -> None:
        """Exports rejected documents to rejected.json"""
        if not docs:
            return
            
        path = os.path.join(self.output_dir, "rejected.json")
        rejected_data = []
        for doc in docs:
            rejected_data.append({
                "doc_id": doc.metadata.doc_id,
                "source": doc.metadata.source,
                "reason": doc.metadata.reject_reason
            })
            
        # Append logic or overwrite; for simplicity, overwriting/creating new array here
        # In a real batch pipeline, you might want to append.
        existing = []
        if os.path.exists(path):
             try:
                 with open(path, 'r', encoding='utf-8') as f:
                     content = f.read()
                     if content:
                        existing = json.loads(content)
             except Exception as e:
                 logger.warning(f"Could not read existing rejected.json: {e}")
                 
        existing.extend(rejected_data)
        
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(existing, f, ensure_ascii=False, indent=2)
            
        logger.info(f"Exported {len(docs)} rejected records to {path}")
        
    def export_report(self, docs: List[ProcessingDocument]) -> None:
        """Exports evaluation reports to eval_report.json"""
        path = os.path.join(self.output_dir, "eval_report.json")
        report_data = []
        
        for doc in docs:
            if doc.eval_details:
                report_data.append({
                    "doc_id": doc.metadata.doc_id,
                    "source": doc.metadata.source,
                    "status": doc.status.value,
                    "final_score": doc.eval_details.final_score,
                    "scores": {
                        "coherence": doc.eval_details.coherence,
                        "completeness": doc.eval_details.completeness,
                        "factual_clarity": doc.eval_details.factual_clarity,
                        "rag_suitability": doc.eval_details.rag_suitability,
                        "language_quality": doc.eval_details.language_quality
                    },
                    "reasoning": doc.eval_details.reasoning,
                     "improve_attempts": doc.metadata.improve_attempts
                })
                
        existing = []
        if os.path.exists(path):
             try:
                 with open(path, 'r', encoding='utf-8') as f:
                     content = f.read()
                     if content:
                        existing = json.loads(content)
             except Exception:
                 pass
                 
        existing.extend(report_data)
        
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(existing, f, ensure_ascii=False, indent=2)
            
        logger.info(f"Exported evaluation report to {path}")

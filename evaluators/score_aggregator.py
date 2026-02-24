from typing import List, Dict, Any
from models import ProcessingDocument, EvalScore, DocStatus
from llm.base_llm import BaseLLM
from .base_evaluator import BaseEvaluator
from .quality_evaluator import QualityEvaluator
from .completeness_evaluator import CompletenessEvaluator
from .rag_evaluator import RAGEvaluator
import logging

logger = logging.getLogger(__name__)

class ScoreAggregator:
    """Runs all evaluators and aggregates their scores based on configured weights."""
    
    def __init__(self, llm: BaseLLM, config: Dict[str, Any]):
        self.config = config.get("evaluation", {})
        self.pass_threshold = self.config.get("pass_threshold", 0.75)
        self.improve_threshold = self.config.get("improve_threshold", 0.40)
        
        self.evaluators: List[BaseEvaluator] = [
            QualityEvaluator(llm),
            CompletenessEvaluator(llm),
            RAGEvaluator(llm)
        ]
        
        # Weights according to README.md scoring rubric
        self.weights = {
            "coherence": 0.25,
            "completeness": 0.25,
            "factual_clarity": 0.20,
            "rag_suitability": 0.20,
            "language_quality": 0.10
        }
        
    def evaluate(self, doc: ProcessingDocument) -> ProcessingDocument:
        """Runs the document against all internal evaluators and assigns a final status."""
        logger.info(f"AI Evaluation started for doc {doc.metadata.doc_id}")
        
        all_scores = {}
        all_hints = []
        all_reasoning = []
        
        # Run all evaluators
        # Note: In a production system, these LLM calls could be done asynchronously
        for evaluator in self.evaluators:
            results = evaluator.evaluate(doc)
            all_scores.update(results)
            
            if "reasoning" in results and results["reasoning"]:
                all_reasoning.append(results["reasoning"])
            if "improvement_hints" in results and results["improvement_hints"]:
                all_hints.extend(results["improvement_hints"])
                
        # Calculate final weighted score
        final_score = 0.0
        total_weight = 0.0
        
        # We define a default score structure. Missing scores count as 0.
        eval_score_obj = EvalScore()
        eval_score_obj.improvement_hints = all_hints
        eval_score_obj.reasoning = " | ".join(all_reasoning)
        
        for criterion, weight in self.weights.items():
            score = all_scores.get(criterion, 0.0)
            setattr(eval_score_obj, criterion, score)
            final_score += score * weight
            total_weight += weight
            
        # Normalize if weights don't sum to exactly 1.0
        if total_weight > 0:
            final_score = final_score / total_weight
            
        eval_score_obj.final_score = final_score
        doc.eval_details = eval_score_obj
        doc.metadata.eval_score = final_score
        
        # Determine status based on thresholds
        if final_score >= self.pass_threshold:
            doc.status = DocStatus.PASS
        elif final_score >= self.improve_threshold:
            doc.status = DocStatus.IMPROVE
        else:
            doc.status = DocStatus.REJECT
            doc.metadata.reject_reason = f"AI Evaluation score too low ({final_score:.2f} < {self.improve_threshold:.2f})"
            
        logger.info(f"Doc {doc.metadata.doc_id} evaluation finished: Score={final_score:.2f}, Status={doc.status.value}")
        return doc

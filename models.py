"""Data schemas for RAGRefiner"""
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Any
from enum import Enum

class DocStatus(Enum):
    PENDING = "PENDING"
    PASS = "PASS"
    IMPROVE = "IMPROVE"
    REJECT = "REJECT"

@dataclass
class EvalScore:
    """Stores the evaluation scores and feedback from the AI evaluator"""
    coherence: float = 0.0
    completeness: float = 0.0
    factual_clarity: float = 0.0
    rag_suitability: float = 0.0
    language_quality: float = 0.0
    
    final_score: float = 0.0
    reasoning: str = ""
    improvement_hints: List[str] = field(default_factory=list)

@dataclass
class DocumentMetadata:
    """Metadata for a document or chunk"""
    doc_id: str
    source: str
    chunk_id: Optional[int] = None
    keywords: List[str] = field(default_factory=list)
    summary: str = ""
    topic_tags: List[str] = field(default_factory=list)
    language: str = "en"
    eval_score: float = 0.0
    created_at: str = ""
    
    # Internal tracking
    improve_attempts: int = 0
    reject_reason: str = ""
    
@dataclass
class ProcessingDocument:
    """Internal representation of a document moving through the pipeline"""
    content: str
    metadata: DocumentMetadata
    status: DocStatus = DocStatus.PENDING
    eval_details: Optional[EvalScore] = None
    chunks: List["ProcessingDocument"] = field(default_factory=list) # Only used after chunking

@dataclass
class FilterResult:
    """Result of a filter operation"""
    passed: bool
    reason: str = ""

import re
from typing import List, Dict, Any
from .base_improver import BaseImprover
from models import ProcessingDocument, DocumentMetadata
import copy

class Chunker(BaseImprover):
    """Splits a document into smaller, sentence-aware chunks."""
    
    def __init__(self, config: Dict[str, Any]):
        chunk_config = config.get("chunking", {})
        self.chunk_size_chars = chunk_config.get("chunk_size", 512) * 4 # Approx 4 chars per token
        self.chunk_overlap_chars = chunk_config.get("chunk_overlap", 64) * 4
        
    def _split_into_sentences(self, text: str) -> List[str]:
        """Simple regex-based sentence splitter."""
        # Split on ., !, ? followed by whitespace or end of string
        sentences = re.split(r'(?<=[.!?])\s+(?=[A-Z])|(?<=[.!?])\s*$', text)
        return [s.strip() for s in sentences if s.strip()]

    def improve(self, doc: ProcessingDocument) -> ProcessingDocument:
        sentences = self._split_into_sentences(doc.content)
        chunks = []
        current_chunk = []
        current_length = 0
        
        for sentence in sentences:
            sentence_len = len(sentence)
            
            # If a single sentence is larger than chunk size, we have to add it anyway
            # (or we could split it further, but keeping logic simple for now)
            if current_length + sentence_len > self.chunk_size_chars and current_chunk:
                # Store current chunk
                chunks.append(" ".join(current_chunk))
                
                # Start new chunk with overlap
                # Walk backwards through current_chunk to fill overlap
                overlap_chunk = []
                overlap_length = 0
                for s in reversed(current_chunk):
                    if overlap_length + len(s) <= self.chunk_overlap_chars:
                        overlap_chunk.insert(0, s)
                        overlap_length += len(s) + 1 # +1 for space
                    else:
                        break
                        
                current_chunk = overlap_chunk
                current_length = overlap_length
                
            current_chunk.append(sentence)
            current_length += sentence_len + 1 # +1 for space
            
        # Add the last chunk
        if current_chunk:
            chunks.append(" ".join(current_chunk))
            
        # Create ProcessingDocument sub-chunks
        doc.chunks = []
        for i, chunk_text in enumerate(chunks):
            # Deep copy metadata so each chunk can have its own without affecting others
            chunk_metadata = copy.deepcopy(doc.metadata)
            chunk_metadata.chunk_id = i
            
            chunk_doc = ProcessingDocument(
                content=chunk_text,
                metadata=chunk_metadata,
                eval_details=doc.eval_details # Carry over evaluation details if any
            )
            doc.chunks.append(chunk_doc)
            
        return doc

import json
from typing import Dict, Any, List
from models import ProcessingDocument

class OutputFormatter:
    """Formats processed and chunked documents into exportable schemas."""
    
    @staticmethod
    def to_langchain_schema(doc: ProcessingDocument) -> Dict[str, Any]:
        """Converts a document chunk into LangChain's Document schema."""
        metadata = {
            "doc_id": doc.metadata.doc_id,
            "source": doc.metadata.source,
            "chunk_id": doc.metadata.chunk_id,
            "keywords": doc.metadata.keywords,
            "summary": doc.metadata.summary,
            "topic_tags": doc.metadata.topic_tags,
            "language": doc.metadata.language,
            "eval_score": doc.metadata.eval_score,
            "created_at": doc.metadata.created_at
        }
        
        return {
            "page_content": doc.content,
            "metadata": metadata
        }
        
    @staticmethod
    def format_batch(docs: List[ProcessingDocument]) -> List[Dict[str, Any]]:
        """Formats a batch of parsed document chunks."""
        formatted_chunks = []
        for doc in docs:
            # We assume input is a list of the *original* passed documents,
            # which each contain their chunks
            if hasattr(doc, 'chunks') and doc.chunks:
                for chunk in doc.chunks:
                    formatted_chunks.append(OutputFormatter.to_langchain_schema(chunk))
            else:
                 # If no chunks, just format the whole doc
                 formatted_chunks.append(OutputFormatter.to_langchain_schema(doc))
                 
        return formatted_chunks

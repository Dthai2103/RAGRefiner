import argparse
import os
import uuid
import logging
from config import CONFIG
from pipeline import RAGPipeline

# Setup basic logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def load_documents_from_dir(directory: str):
    """Loads all text files from a directory."""
    docs = []
    if not os.path.exists(directory):
        logger.error(f"Input directory {directory} does not exist.")
        return docs
        
    for filename in os.listdir(directory):
         if filename.endswith(".txt") or filename.endswith(".md"):
             filepath = os.path.join(directory, filename)
             try:
                 with open(filepath, 'r', encoding='utf-8') as f:
                     content = f.read()
                     doc_id = str(uuid.uuid4())[:8] # Short UUID for simpler logging
                     docs.append((content, doc_id, filename))
             except Exception as e:
                 logger.error(f"Failed to read file {filename}: {e}")
    return docs

def main():
    parser = argparse.ArgumentParser(description="RAGRefiner - Document Processing Pipeline")
    parser.add_argument("--input", "-i", type=str, required=True, help="Input directory containing .txt or .md files")
    parser.add_argument("--output", "-o", type=str, required=True, help="Output directory for processed data")
    
    args = parser.parse_args()
    
    # Initialize pipeline
    pipeline = RAGPipeline(CONFIG, args.output)
    
    # Load and process
    docs_input = load_documents_from_dir(args.input)
    if not docs_input:
         logger.info("No documents to process. Exiting.")
         return
         
    stats = pipeline.process_batch(docs_input)
    
    print("\n" + "="*40)
    print("🎉 Pipeline Execution Complete 🎉")
    print("="*40)
    for k, v in stats.items():
        print(f"{k}: {v}")
    print(f"\nOutputs written to: {args.output}")

if __name__ == "__main__":
    main()

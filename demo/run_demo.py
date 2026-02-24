import os
import sys

# Add parent directory to path so we can import modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import CONFIG
from pipeline import RAGPipeline
import logging

logging.basicConfig(level=logging.INFO, format='%(levelname)s - %(message)s')

def main():
    print("🚀 Starting RAGRefiner Demo 🚀")
    
    # Paths relative to the script location
    base_dir = os.path.dirname(os.path.abspath(__file__))
    input_dir = os.path.join(base_dir, "sample_data")
    output_dir = os.path.join(base_dir, "output")
    
    os.makedirs(output_dir, exist_ok=True)
    
    # Initialize pipeline
    print(f"\nInitializing pipeline with model {CONFIG['llm']['model']}...")
    pipeline = RAGPipeline(CONFIG, output_dir)
    
    # Load docs directly for the demo
    docs_input = []
    for filename in ["good_doc.txt", "noisy_doc.txt", "duplicate_doc.txt"]:
        filepath = os.path.join(input_dir, filename)
        if os.path.exists(filepath):
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
                docs_input.append((content, f"demo-{filename.split('.')[0]}", filename))
        else:
             print(f"Warning: Demo file {filename} not found.")

    if not docs_input:
        print("No demo files found. Cannot run demo.")
        return

    print(f"\nProcessing {len(docs_input)} demo documents...")
    stats = pipeline.process_batch(docs_input)
    
    print("\n" + "="*40)
    print("📊 Demo Execution Complete 📊")
    print("="*40)
    for k, v in stats.items():
        print(f"{k}: {v}")
    
    print(f"\nOutputs written to: {output_dir}")
    print("Check documents.jsonl for passing chunks, and eval_report.json for AI scoring details.")

if __name__ == "__main__":
    main()

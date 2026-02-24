# RAGRefiner Configuration

CONFIG = {
    "llm": {
        "model": "llama3.2",                    # change model here
        "base_url": "http://localhost:11434",
        "temperature": 0.3,
        "max_retries": 3,
        "timeout": 60, # seconds
    },
    "evaluation": {
        "pass_threshold": 0.75,                  # PASS if score >= 0.75
        "improve_threshold": 0.40,               # IMPROVE if score >= 0.40
        "max_improve_attempts": 2,
    },
    "chunking": {
        "chunk_size": 512,                       # tokens (approximate)
        "chunk_overlap": 64,
    },
}

# RAG Data Pipeline 🚀

Hệ thống pipeline tự động **lọc → đánh giá → cải thiện** document, xuất ra định dạng sẵn sàng cho RAG system. Dùng **Ollama local** làm AI engine — hoàn toàn offline, không cần API key.

---

## ✨ Tính năng

- 🔍 **Lọc thông minh** — Loại bỏ tài liệu kém chất lượng, trùng lặp, lạc đề trước khi gọi AI
- 🤖 **AI tự đánh giá** — Ollama chấm điểm 5 tiêu chí chất lượng theo thang 0–1
- 📝 **AI tự cải thiện** — Tự động rewrite + re-evaluate vòng lặp tối đa 2 lần
- 🏷️ **Làm giàu metadata** — AI tự tạo keywords, summary, topic tags
- ✂️ **Smart chunking** — Tách chunk theo ranh giới câu, không cắt giữa ý
- 📦 **Export chuẩn RAG** — Tương thích LangChain `Document` và LlamaIndex `TextNode`

---

## 🏗️ Kiến trúc

```
Input (.txt / .md / .pdf)
        │
        ▼
┌──────────────────────────────────────┐
│  Module 1 — FILTERS (rule-based)     │
│  quality → dedup → relevance         │──► REJECT (ngắn/trùng/lạc đề)
└───────────────────┬──────────────────┘
                    │ passed
                    ▼
┌──────────────────────────────────────┐
│  Module 2 — EVALUATORS (AI)          │
│  quality + completeness + rag_fit    │──► REJECT nếu score < 0.40
└───────────────────┬──────────────────┘
                    │ IMPROVE (0.40–0.75)
                    ▼
┌──────────────────────────────────────┐
│  Module 3 — IMPROVERS (AI)           │
│  clean → rewrite → re-eval (max 2×)  │──► REJECT nếu vẫn thấp
└───────────────────┬──────────────────┘
                    │ PASS (≥ 0.75)
                    ▼
┌──────────────────────────────────────┐
│  Module 4 — OUTPUT                   │
│  chunk + metadata → export JSONL     │
└──────────────────────────────────────┘
```

---

## 📁 Cấu trúc dự án

```
rag_pipeline/
├── config.py                 # Cấu hình LLM, thresholds, chunking
├── models.py                 # Data schemas dùng chung
├── pipeline.py               # Orchestrator end-to-end
├── main.py                   # CLI entry point
│
├── llm/                      # Ollama local layer
│   ├── base_llm.py           # Abstract + retry/timeout
│   ├── ollama_llm.py         # HTTP → Ollama /api/generate
│   └── __init__.py           # create_llm(config) factory
│
├── filters/                  # Module 1: Pre-filter (rule-based)
│   ├── base_filter.py
│   ├── quality_filter.py     # Độ dài + noise ratio
│   ├── dedup_filter.py       # MD5 exact + Jaccard near-dup
│   ├── relevance_filter.py   # Keyword/topic matching
│   └── filter_pipeline.py
│
├── evaluators/               # Module 2: AI Self-Evaluation
│   ├── base_evaluator.py
│   ├── quality_evaluator.py  # coherence, language_quality
│   ├── completeness_evaluator.py  # completeness, factual_clarity
│   ├── rag_evaluator.py      # rag_suitability, chunk density
│   └── score_aggregator.py   # Weighted sum → PASS/IMPROVE/REJECT
│
├── improvers/                # Module 3: AI Improvement
│   ├── base_improver.py
│   ├── text_cleaner.py       # Rule-based: xóa HTML, chuẩn hoá
│   ├── chunker.py            # Sentence-aware chunking + overlap
│   ├── metadata_enricher.py  # AI: keywords, summary, tags
│   └── improve_pipeline.py   # rewrite → re-eval loop
│
├── output/                   # Module 4: Export
│   ├── formatter.py          # LangChain / LlamaIndex schema
│   └── exporter.py           # Ghi JSONL / JSON / Markdown
│
└── demo/
    ├── sample_data/
    │   ├── good_doc.txt
    │   ├── noisy_doc.txt
    │   └── duplicate_doc.txt
    └── run_demo.py
```

---

## ⚙️ Cài đặt

### 1. Cài Ollama

```bash
# Tải tại: https://ollama.com/download
ollama pull llama3.2
```

> Có thể dùng model khác: `mistral`, `phi3`, `qwen2.5`, `deepseek-r1`

### 2. Python dependencies

```bash
pip install pyyaml
# Không cần gì thêm — urllib có sẵn trong stdlib Python
```

---

## 🚀 Sử dụng

### Chạy demo nhanh

```bash
cd rag_pipeline
python demo/run_demo.py
```

Kết quả mong đợi:

| File | Kết quả |
|---|---|
| `good_doc.txt` | ✅ PASS → 3 chunks exported |
| `noisy_doc.txt` | 🔄 IMPROVE → AI rewrite → ✅ PASS → 2 chunks exported |
| `duplicate_doc.txt` | ❌ REJECT (dedup filter) |

### CLI

```bash
python main.py --input ./my_docs/ --output ./output/
```

### Output files

```
output/
├── documents.jsonl    # RAG-ready chunks (1 dòng = 1 chunk)
├── eval_report.json   # Điểm đánh giá từng document
└── rejected.json      # Document bị loại + lý do
```

---

## 📊 Schema Output (LangChain)

Mỗi dòng trong `documents.jsonl`:

```json
{
  "page_content": "Nội dung chunk...",
  "metadata": {
    "doc_id": "b3f1a...",
    "chunk_id": 0,
    "source": "my_file.txt",
    "keywords": ["RAG", "vector search", "embedding"],
    "summary": "Tóm tắt ngắn gọn nội dung chunk.",
    "topic_tags": ["AI", "NLP"],
    "language": "vi",
    "eval_score": 0.82,
    "created_at": "2026-02-24T04:30:00Z"
  }
}
```

### Load vào LangChain

```python
import json
from langchain.schema import Document

with open("output/documents.jsonl") as f:
    docs = [Document(**json.loads(line)) for line in f]
```

---

## 🎛️ Cấu hình ([config.py](file:///d:/New%20folder/rag_pipeline/config.py))

```python
CONFIG = {
    "llm": {
        "model": "llama3.2",                    # đổi model tại đây
        "base_url": "http://localhost:11434",
        "temperature": 0.3,
    },
    "evaluation": {
        "pass_threshold": 0.75,                  # PASS nếu score ≥ 0.75
        "improve_threshold": 0.40,               # IMPROVE nếu score ≥ 0.40
        "max_improve_attempts": 2,
    },
    "chunking": {
        "chunk_size": 512,                       # tokens
        "chunk_overlap": 64,
    },
}
```

---

## 🤖 Scoring Rubric (AI Evaluator)

| Tiêu chí | Trọng số | Mô tả |
|---|---|---|
| `coherence` | 25% | Mạch lạc, câu liên kết tốt |
| `completeness` | 25% | Thông tin đầy đủ, không bị cắt dở |
| `factual_clarity` | 20% | Rõ ràng, không mơ hồ |
| `rag_suitability` | 20% | Phù hợp để chunk & retrieve |
| `language_quality` | 10% | Chính tả, ngữ pháp |

AI trả về JSON có cấu trúc:

```json
{
  "scores": { "coherence": 0.85, "completeness": 0.70, ... },
  "reasoning": "Document mạch lạc nhưng thiếu kết luận.",
  "improvement_hints": ["Bổ sung đoạn kết luận", "Làm rõ thuật ngữ ở đoạn 2"]
}
```

---

## 🔄 Self-feedback Loop

```
text_cleaner
    → AI rewrite (dùng improvement_hints từ evaluator)
    → re-evaluate
    → score ≥ 0.75 ? PASS
    : attempts < 2  ? loop lại
    : REJECT + ghi vào rejected.json
```

---

## 📋 Requirements

- Python 3.10+
- Ollama đang chạy (`ollama serve`)
- `pyyaml` (optional, chỉ cần nếu dùng config file YAML)

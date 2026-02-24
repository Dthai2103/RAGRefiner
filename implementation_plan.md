# RAG Data Pipeline — Implementation Plan (Ollama Local)

Pipeline 4 module xử lý document cho RAG system, dùng **Ollama local** làm AI engine.

---

## Kiến trúc & Flow

```
Input (.txt / .md / .pdf)
        │
        ▼
┌──────────────────────────────────────┐
│  Module 1 — FILTERS (rule-based)     │
│  base → quality → dedup → relevance  │──► REJECT (quá ngắn/trùng/lạc đề)
└───────────────────┬──────────────────┘
                    │ passed
                    ▼
┌──────────────────────────────────────┐
│  Module 2 — EVALUATORS (AI)          │
│  quality + completeness + rag        │
│  → score_aggregator                  │──► REJECT nếu score < 0.40
└───────────────────┬──────────────────┘
                    │ IMPROVE (0.40–0.75)
                    ▼
┌──────────────────────────────────────┐
│  Module 3 — IMPROVERS (AI)           │
│  cleaner → AI rewrite → metadata     │
│  → chunker → re-evaluate (max 2x)    │──► REJECT nếu vẫn thấp
└───────────────────┬──────────────────┘
                    │ PASS (≥ 0.75)
                    ▼
┌──────────────────────────────────────┐
│  Module 4 — OUTPUT                   │
│  formatter → exporter                │──► documents.jsonl / eval_report.json
└──────────────────────────────────────┘
```

---

## Project Structure

```
d:\New folder\rag_pipeline\
├── config.py                 # Tất cả cấu hình (LLM, thresholds, chunking…)
├── models.py                 # Data schemas dùng chung
├── pipeline.py               # Orchestrator end-to-end
├── main.py                   # CLI: python main.py --input docs/ --output out/
│
├── llm/                      # [THÊM] Ollama local layer
│   ├── __init__.py           # create_llm(config) factory
│   ├── base_llm.py           # Abstract + retry/timeout
│   └── ollama_llm.py         # HTTP call → Ollama /api/generate
│
├── filters/
│   ├── base_filter.py        # Abstract BaseFilter
│   ├── quality_filter.py     # Độ dài + noise ratio (rule-based)
│   ├── dedup_filter.py       # MD5 exact + Jaccard near-dup
│   ├── relevance_filter.py   # Keyword/topic matching (rule-based)
│   └── filter_pipeline.py   # Chạy filters tuần tự
│
├── evaluators/
│   ├── base_evaluator.py     # Abstract BaseEvaluator + EvalScore
│   ├── quality_evaluator.py  # AI: coherence + language_quality
│   ├── completeness_evaluator.py  # AI: completeness + factual_clarity
│   ├── rag_evaluator.py      # AI: rag_suitability + chunk density
│   └── score_aggregator.py  # Tổng hợp → final_score → PASS/IMPROVE/REJECT
│
├── improvers/
│   ├── base_improver.py      # Abstract BaseImprover
│   ├── text_cleaner.py       # Rule-based: xóa HTML, chuẩn hoá whitespace
│   ├── chunker.py            # Sentence-aware chunking + overlap
│   ├── metadata_enricher.py  # AI: keywords, summary, topic_tags
│   └── improve_pipeline.py  # AI rewrite → re-eval loop (max 2 lần)
│
├── output/
│   ├── formatter.py          # Chuyển chunks → LangChain / LlamaIndex schema
│   └── exporter.py           # Ghi JSONL, JSON, Markdown
│
└── demo/
    ├── sample_data/
    │   ├── good_doc.txt      # Document tốt → PASS ngay
    │   ├── noisy_doc.txt     # Document kém → IMPROVE → PASS
    │   └── duplicate_doc.txt # Bản sao → REJECT (dedup)
    └── run_demo.py           # Demo end-to-end
```

---

## Chi tiết từng module

### `llm/` — Ollama Local Layer

| File | Vai trò |
|---|---|
| [base_llm.py](file:///d:/New%20folder/rag_pipeline/llm/base_llm.py) | Abstract `generate(prompt) → str` + retry 3 lần |
| [ollama_llm.py](file:///d:/New%20folder/rag_pipeline/llm/ollama_llm.py) | POST `http://localhost:11434/api/generate` bằng stdlib `urllib` (zero deps) |
| [__init__.py](file:///d:/New%20folder/rag_pipeline/llm/__init__.py) | `create_llm(config)` factory function |

LLM instance được **inject** vào evaluators và improvers khi khởi tạo.

---

### `filters/` — Pre-filter (Rule-based, không dùng LLM)

| File | Logic |
|---|---|
| `base_filter.py` | `filter(doc) → FilterResult` |
| [quality_filter.py](file:///d:/New%20folder/rag_pipeline/filters/quality_filter.py) | min/max chars, noise ratio ≤ 35% |
| [dedup_filter.py](file:///d:/New%20folder/rag_pipeline/filters/dedup_filter.py) | MD5 hash + Jaccard trigram ≥ 0.85 |
| `relevance_filter.py` | Keyword overlap nếu `allowed_keywords` được cấu hình |
| [filter_pipeline.py](file:///d:/New%20folder/rag_pipeline/filters/filter_pipeline.py) | `run_batch(docs)` → (passed, rejected) |

---

### `evaluators/` — AI Self-Evaluation (dùng Ollama)

Mỗi evaluator gửi prompt riêng, trả về JSON điểm số:

| Evaluator | Tiêu chí chấm |
|---|---|
| `quality_evaluator.py` | `coherence` (0–1), `language_quality` (0–1) |
| `completeness_evaluator.py` | `completeness` (0–1), `factual_clarity` (0–1) |
| `rag_evaluator.py` | `rag_suitability` (0–1) — chunk-ability, info density |
| `score_aggregator.py` | Weighted sum → `final_score`, quyết định PASS/IMPROVE/REJECT |

**Thresholds:**
- `PASS` ≥ 0.75
- `IMPROVE` 0.40–0.75
- `REJECT` < 0.40

---

### `improvers/` — AI Improvement (dùng Ollama)

| File | Vai trò |
|---|---|
| `text_cleaner.py` | Rule-based: xóa HTML/URL thừa, chuẩn hoá whitespace, encoding |
| [chunker.py](file:///d:/New%20folder/rag_pipeline/improvers/chunker.py) | Tách sentence-aware, `chunk_size=512 tokens`, `overlap=64 tokens` |
| `metadata_enricher.py` | Ollama tạo `keywords`, `summary`, `topic_tags`, detect `language` |
| `improve_pipeline.py` | `cleaner → AI rewrite → re-evaluate` (lặp tối đa 2 lần) |

**Self-feedback loop:**
```
text_cleaner → AI rewrite (hints từ evaluator)
    → re-evaluate
    → if score ≥ 0.75: PASS
    → elif attempts < 2: loop lại
    → else: REJECT + flag manual review
```

---

### `output/` — RAG-ready Export

**LangChain schema (`documents.jsonl`):**
```json
{
  "page_content": "Nội dung chunk...",
  "metadata": {
    "doc_id": "uuid", "chunk_id": 0, "source": "file.txt",
    "keywords": ["từ khóa"], "summary": "...", "topic_tags": ["chủ đề"],
    "language": "vi", "eval_score": 0.82, "created_at": "..."
  }
}
```

**Báo cáo (`eval_report.json`):** điểm từng tiêu chí, lý do, số lần cải thiện.

**Danh sách loại (`rejected.json`):** doc_id + lý do reject.

---

## Yêu cầu hệ thống

```bash
# Cài Ollama
https://ollama.com/download  →  ollama pull llama3.2

# Python packages (tối thiểu)
pip install pyyaml           # chỉ cần nếu muốn dùng config.yaml
# Không cần gì thêm — urllib có sẵn trong stdlib
```

---

## Verification

```bash
python demo/run_demo.py
# → good_doc.txt   : PASS  | 3 chunks exported
# → noisy_doc.txt  : IMPROVE → rewrite → PASS | 2 chunks exported
# → duplicate_doc.txt: REJECT (dedup filter)

python main.py --input ./my_docs/ --output ./output/
```

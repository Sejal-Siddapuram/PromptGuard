# PromptGuard

A multi-layer prompt injection detection system built around LLM-integrated pipelines. Sits in front of an LLM (Ollama) and intercepts adversarial inputs before they reach the model.

Built as part of a research internship at the PESU Innovation Lab, in collaboration with Akamai Technologies.

---

## How it works

Three detection tiers run on every incoming prompt:

**Tier 1 — Regex** pattern matching across categories like instruction overrides, system prompt extraction attempts, jailbreaks, encoding tricks, and agent manipulation. Fast, zero-latency, no model required.

**Tier 2 — Semantic search** against a ChromaDB vector store populated with known attack and benign prompt datasets. Uses weighted similarity voting between attack and benign vectors to compute an injection probability score.

**Tier 3 — LoRA classifier** fine-tuned Qwen3-0.6B model (`abedegno/prompt-injection-classifier-qwen3-0p6b`) for per-prompt unsafe/safe classification. Optional — falls back gracefully to the two-tier pipeline if disabled or unavailable.

All three scores are combined into a final risk score. If a prompt crosses the threshold, it's blocked before Ollama ever sees it.

---

## Stack

- **FastAPI** — detection API and middleware guardrail
- **Ollama** (`qwen2.5:0.5b`) — the protected LLM
- **ChromaDB** — vector store for semantic search
- **Streamlit** — SIEM-style dashboard for live monitoring and analytics
- **sentence-transformers** (`all-MiniLM-L6-v2`) — embeddings for semantic search
- **peft + transformers** — LoRA adapter loading

Everything runs in Docker.

---

## Prerequisites

- Docker + Docker Compose
- NVIDIA GPU recommended (Ollama will fall back to CPU if not available)
- A HuggingFace account with a read token — needed to download the LoRA model and some datasets

---

## Setup

### 1. Clone the repo

```bash
git clone https://github.com/Sejal-Siddapuram/PromptGuard.git
cd PromptGuard
```

### 2. HuggingFace token

The LoRA classifier and some datasets require HuggingFace access. Generate a token at https://huggingface.co/settings/tokens (read-only is fine).

Add it to your `docker-compose.yml` under the `fastapi` service environment:

```yaml
environment:
  - OLLAMA_URL=http://ollama:11434/api/generate
  - HF_TOKEN=your_token_here
```

Or set it as an env variable on your machine and reference it:

```yaml
environment:
  - HF_TOKEN=${HF_TOKEN}
```

### 3. Start the containers

```bash
docker compose up --build -d
```

### 4. Pull the LLM

```bash
docker exec ollama ollama pull qwen2.5:0.5b
```

### 5. Populate the vector store

This downloads several datasets (HackAPrompt, LLMail, Databricks Dolly, LMSYS Chat) and builds the ChromaDB index. Takes a few minutes the first time. Run this from the project root — the `chroma_db/` folder is mounted into the container so it persists across rebuilds.

```bash
python populate_db.py
```

---

## Usage

| Service     | URL |

| Dashboard | http://localhost:8501 |
| FastAPI   | http://localhost:8000 |
| Ollama    | http://localhost:11434 |

Send a chat request:

```bash
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"prompt": "What is the capital of France?"}'
```

---

## Environment variables

These can be set under the `fastapi` service in `docker-compose.yml`:

| Variable      | Default                            | Description |

| `OLLAMA_URL`  | `http://ollama:11434/api/generate` | Ollama endpoint |
| `OLLAMA_MODEL`| `qwen2.5:0.5b`                    | Model to use |
| `LORA_ENABLED`| `true` | Set to `false` to disable Tier 3 and run two-tier only |
| `LORA_DEVICE` | `cpu` | `cpu` or `cuda` |
| `LORA_THRESHOLD` | `0.10` | Probability cutoff for LoRA unsafe classification |
| `CHROMA_COLLECTION` | `prompts` | ChromaDB collection name |
| `HF_TOKEN` | — | Your HuggingFace read token |

---

## Disabling LoRA (low-resource environments)

If you're running without a GPU or want faster startup, set `LORA_ENABLED=false` in your compose file. The system falls back to Tier 1 + Tier 2 only. Detection still works, just without the neural classifier layer.

---

## Rebuilding after code changes

```bash
# Rebuild just the FastAPI container
docker compose up --build -d fastapi

# Full reset including volumes (re-populate DB after this)
docker compose down -v
docker compose up --build -d
```

---

## Project structure

```
.
├── main.py                  # FastAPI app, /chat, /status endpoints
├── populate_db.py           # Builds the ChromaDB vector store
├── dashboard.py             # Streamlit SIEM dashboard
├── detectors/
│   ├── decision.py          # Combines all three tiers into a final verdict
│   ├── middleware.py        # FastAPI middleware — intercepts /chat requests
│   ├── regex_detector.py    # Tier 1: pattern matching
│   ├── semantics.py         # Tier 2: ChromaDB vector search
│   └── lora_classifier.py   # Tier 3: LoRA fine-tuned classifier
├── requirements.txt
├── requirements_dashboard.txt
├── Dockerfile
└── docker-compose.yml
```

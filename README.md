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

Before you start, make sure you have:

- [Docker Desktop](https://www.docker.com/products/docker-desktop/) installed and running
- Python 3.10+ installed locally (needed to run `populate_db.py`)
- A HuggingFace account with a read token (instructions below)

---

## Setup

### 1. Clone the repo

```bash
git clone https://github.com/Sejal-Siddapuram/PromptGuard.git
cd PromptGuard
```

### 2. Get a HuggingFace token

Some datasets and the LoRA model are gated on HuggingFace and require authentication.

1. Go to https://huggingface.co/settings/tokens
2. Click **New token**, select **Read** access, generate it and copy it
3. Accept access for these two datasets (just click the button on each page):
   - https://huggingface.co/datasets/hackaprompt/hackaprompt-dataset
   - https://huggingface.co/datasets/lmsys/lmsys-chat-1m

### 3. Configure your GPU

The default `docker-compose.yml` is set up for NVIDIA GPUs. Check which case applies to you:

**If you have an NVIDIA GPU** — no changes needed, it'll use it automatically.

**If you have a different GPU or no GPU** — open `docker-compose.yml` and remove the `deploy` block from the `ollama` service:

```yaml
# delete these lines from docker-compose.yml if you don't have an NVIDIA GPU
deploy:
  resources:
    reservations:
      devices:
        - driver: nvidia
          count: 1
          capabilities: [gpu]
```

Ollama will fall back to CPU automatically. Everything still works, inference will just be slower.

### 4. Add your HuggingFace token to docker-compose.yml

Open `docker-compose.yml` and find the `fastapi` service. Add your token to the environment section:

```yaml
environment:
  - OLLAMA_URL=http://ollama:11434/api/generate
  - HF_TOKEN=your_token_here        # replace this with your actual token
```

### 5. Start the containers

```bash
docker compose up --build -d
```

This builds the FastAPI image and starts all three containers (Ollama, PromptGuard, Dashboard). Wait for it to finish before moving on.

### 6. Pull the LLM

```bash
docker exec ollama ollama pull qwen2.5:0.5b
```

This downloads the language model into Ollama. Takes a few minutes depending on your connection (~400MB).

### 7. Install Python dependencies locally

The vector store is populated from your local machine, not inside the container. Install the required packages first:

```bash
pip install sentence-transformers chromadb datasets huggingface_hub
```

### 8. Populate the vector store

This is a one-time setup step. It downloads several attack and benign prompt datasets and builds the ChromaDB index that the semantic search layer uses.

First log in to HuggingFace so the gated datasets can be accessed:

```bash
python -c "from huggingface_hub import login; login('your_token_here')"
```

Then run:

```bash
python populate_db.py
```

This takes several minutes. The `chroma_db/` folder is mounted as a Docker volume so it persists across container rebuilds — **you only need to do this once**. The only time you'd need to rerun it is if you explicitly wipe your volumes with `docker compose down -v`.

---

## You're done

Open these in your browser:

| Service   | URL                    |
|-----------|------------------------|
| Dashboard | http://localhost:8501  |
| FastAPI   | http://localhost:8000  |
| Ollama    | http://localhost:11434 |

Test it with a benign prompt:

```bash
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"prompt": "What is the capital of France?"}'
```

---

## Environment variables

These can all be set under the `fastapi` service in `docker-compose.yml`:

| Variable             | Default                              | Description                                            |
|----------------------|--------------------------------------|--------------------------------------------------------|
| `OLLAMA_URL`         | `http://ollama:11434/api/generate`   | Ollama endpoint                                        |
| `OLLAMA_MODEL`       | `qwen2.5:0.5b`                       | Model to use                                           |
| `LORA_ENABLED`       | `true`                               | Set to `false` to disable Tier 3 and run two-tier only |
| `LORA_DEVICE`        | `cpu`                                | `cpu` or `cuda`                                        |
| `LORA_THRESHOLD`     | `0.10`                               | Probability cutoff for LoRA unsafe classification      |
| `CHROMA_COLLECTION`  | `prompts`                            | ChromaDB collection name                               |
| `HF_TOKEN`           | —                                    | Your HuggingFace read token                            |

---

## Disabling LoRA (low-resource environments)

If you're running without a GPU or want faster startup, set `LORA_ENABLED=false` in your `docker-compose.yml` under the `fastapi` environment section. The system falls back to Tier 1 + Tier 2 only. Detection still works, just without the neural classifier layer.

---

## Rebuilding after code changes

```bash
# Rebuild just the FastAPI container after code changes
docker compose up --build -d fastapi

# Full reset including volumes — you'll need to repopulate the DB after this
docker compose down -v
docker compose up --build -d
```

---

## Project structure

```
.
├── main.py                      # FastAPI app, /chat, /status endpoints
├── populate_db.py               # Builds the ChromaDB vector store (run once)
├── dashboard.py                 # Streamlit SIEM dashboard
├── detectors/
│   ├── decision.py              # Combines all three tiers into a final verdict
│   ├── middleware.py            # FastAPI middleware — intercepts /chat requests
│   ├── regex_detector.py        # Tier 1: pattern matching
│   ├── semantics.py             # Tier 2: ChromaDB vector search
│   └── lora_classifier.py       # Tier 3: LoRA fine-tuned classifier
├── tests/
│   ├── realworld_benchmark.py   # 90/10 split benchmark on jayavibhav test set
│   └── threshold_tuner.py       # Sweeps risk thresholds to find optimal cutoff
├── requirements.txt
├── requirements_dashboard.txt
├── Dockerfile
└── docker-compose.yml
```
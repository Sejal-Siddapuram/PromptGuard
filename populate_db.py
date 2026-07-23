import os

import chromadb
from datasets import load_dataset
from sentence_transformers import SentenceTransformer

COLLECTION_NAME = os.environ.get("CHROMA_COLLECTION", "prompts")
BATCH_SIZE = int(os.environ.get("INGEST_BATCH_SIZE", "128"))

# targets: 10k malicious, 10k benign
MAX_HACK        = 6000
MAX_LLMAIL      = 5000
MAX_EXTRACTION  = 100
MAX_HARD        = 2000
MAX_DOLLY       = 4000
MAX_LMSYS       = 4000
MAX_ALPACA      = 2000

print("Loading sentence embedding model...")
embed_model = SentenceTransformer("all-MiniLM-L6-v2")
db_client = chromadb.PersistentClient(path="./chroma_db")

for name in {"attacks", COLLECTION_NAME}:
    try:
        db_client.delete_collection(name)
        print(f"Removed old collection: {name}")
    except Exception:
        pass

col = db_client.create_collection(
    name=COLLECTION_NAME,
    metadata={"hnsw:space": "cosine"},
)
seen = set()


def normalize(text: str) -> str:
    return " ".join(text.lower().split())


def is_dupe(text: str) -> bool:
    n = normalize(text)
    if n in seen:
        return True
    seen.add(n)
    return False


def flush_batch(rows: list[dict]) -> None:
    if not rows:
        return
    docs = [r["prompt"] for r in rows]
    embeddings = embed_model.encode(docs, normalize_embeddings=True, show_progress_bar=False).tolist()
    col.add(
        ids=[r["id"] for r in rows],
        documents=docs,
        embeddings=embeddings,
        metadatas=[r["metadata"] for r in rows],
    )


def ingest(rows, source: str, label: int, limit: int, get_text) -> int:
    count = 0
    batch = []
    for row in rows:
        if count >= limit:
            break
        text = get_text(row).strip()
        if not text or is_dupe(text):
            continue
        batch.append({
            "id": f"{source}_{count}",
            "prompt": text,
            "metadata": {"source": source, "label": label},
        })
        count += 1
        if len(batch) >= BATCH_SIZE:
            flush_batch(batch)
            batch = []
            print(f"  {source}: {count}")
    flush_batch(batch)
    return count


def first_user_turn(row: dict) -> str:
    convo = row.get("conversation") or row.get("conversations") or []
    for msg in convo:
        role = str(msg.get("role", msg.get("from", ""))).lower()
        if role in {"user", "human"}:
            return str(msg.get("content", msg.get("value", "")))
    return ""


counts = {}

# --- MALICIOUS ---

print("\n[MALICIOUS] Loading HackAPrompt dataset...")
try:
    rows = load_dataset("hackaprompt/hackaprompt-dataset", split="train")
    counts["hackaprompt"] = ingest(rows, "hackaprompt", 1, MAX_HACK, lambda r: str(r.get("user_input", "")))
except Exception as exc:
    print(f"[ERROR] Skipping HackAPrompt: {exc}")
    counts["hackaprompt"] = 0

print("\n[MALICIOUS] Loading LLMail dataset...")
try:
    ds = load_dataset("microsoft/llmail-inject-challenge")
    counts["llmail"] = ingest(ds["Phase1"], "llmail", 1, MAX_LLMAIL, lambda r: str(r.get("body", "")))
except Exception as exc:
    print(f"[ERROR] Skipping LLMail: {exc}")
    counts["llmail"] = 0

print("\n[MALICIOUS] Loading hard attacks dataset...")
try:
    with open("hard_attacks.txt", "r", encoding="utf-8") as fh:
        rows = ({"text": line.strip()} for line in fh)
        counts["hard_attacks"] = ingest(rows, "hard_attacks", 1, MAX_HARD, lambda r: r["text"])
except OSError as exc:
    print(f"[WARNING] Skipping hard attacks: {exc}")
    counts["hard_attacks"] = 0

print("\n[MALICIOUS] Loading custom extraction attacks...")
try:
    with open("extraction_prompts.txt", "r", encoding="utf-8") as fh:
        rows = ({"text": line.strip()} for line in fh)
        counts["custom_extraction"] = ingest(rows, "custom_extraction", 1, MAX_EXTRACTION, lambda r: r["text"])
except OSError as exc:
    print(f"[WARNING] Skipping custom extraction attacks: {exc}")
    counts["custom_extraction"] = 0

# --- BENIGN ---

print("\n[BENIGN] Loading curated educational benign prompts...")
try:
    with open("educational_benign_prompts.txt", "r", encoding="utf-8") as fh:
        rows = ({"text": line.strip()} for line in fh)
        counts["educational_benign"] = ingest(rows, "educational_benign", 0, 1_000_000, lambda r: r["text"])
except OSError as exc:
    print(f"[WARNING] Skipping educational benign prompts: {exc}")
    counts["educational_benign"] = 0

print("\n[BENIGN] Loading Databricks Dolly dataset...")
try:
    rows = load_dataset("databricks/databricks-dolly-15k", split="train")
    counts["databricks_dolly"] = ingest(
        rows, "databricks_dolly", 0, MAX_DOLLY,
        lambda r: "\n\n".join(
            p for p in (str(r.get("instruction", "")), str(r.get("context", ""))) if p.strip()
        ),
    )
except Exception as exc:
    print(f"[ERROR] Skipping Databricks Dolly: {exc}")
    counts["databricks_dolly"] = 0

print("\n[BENIGN] Loading LMSYS Chat dataset...")
try:
    rows = load_dataset("lmsys/lmsys-chat-1m", split="train", streaming=True)
    counts["lmsys_chat"] = ingest(rows, "lmsys_chat", 0, MAX_LMSYS, first_user_turn)
except Exception as exc:
    print(f"[ERROR] Skipping LMSYS Chat: {exc}")
    counts["lmsys_chat"] = 0

print("\n[BENIGN] Loading Alpaca dataset...")
try:
    rows = load_dataset("tatsu-lab/alpaca", split="train")
    counts["alpaca"] = ingest(
        rows, "alpaca", 0, MAX_ALPACA,
        lambda r: "\n\n".join(
            p for p in (str(r.get("instruction", "")), str(r.get("input", ""))) if p.strip()
        ),
    )
except Exception as exc:
    print(f"[ERROR] Skipping Alpaca: {exc}")
    counts["alpaca"] = 0

# --- SUMMARY ---

total_malicious = sum(counts[k] for k in ["hackaprompt", "llmail", "hard_attacks", "custom_extraction"])
total_benign = sum(counts[k] for k in ["educational_benign", "databricks_dolly", "lmsys_chat", "alpaca"])

print("\n" + "="*50)
print("Vector store population finished")
print("="*50)
for source, n in counts.items():
    print(f"  {source}: {n}")
print(f"\nTotal malicious : {total_malicious}")
print(f"Total benign    : {total_benign}")
print(f"Total unique    : {len(seen)}")
print(f"Collection count: {col.count()}")

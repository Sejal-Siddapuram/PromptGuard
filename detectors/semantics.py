import os

import chromadb
from sentence_transformers import SentenceTransformer

COLLECTION_NAME = os.environ.get("CHROMA_COLLECTION", "prompts")
CHROMA_PATH = os.environ.get("CHROMA_PATH", "./chroma_db")
TOP_K = int(os.environ.get("SEMANTIC_TOP_K", "20"))

model = SentenceTransformer("all-MiniLM-L6-v2")
client = chromadb.PersistentClient(path=CHROMA_PATH)

try:
    collection = client.get_collection(COLLECTION_NAME)
except Exception as exc:
    print(f"[WARNING] Could not load {COLLECTION_NAME} collection: {exc}")
    collection = None


def _avg(vals: list[float]) -> float:
    return sum(vals) / len(vals) if vals else 0.0


def _weighted_sim(sims: list[float]) -> float:
    if not sims:
        return 0.0
    top1 = sims[0]
    top5 = _avg(sims[:5])
    top20 = _avg(sims)
    return 0.5 * top1 + 0.3 * top5 + 0.2 * top20


def semantic_search(prompt: str, top_k: int = TOP_K) -> dict:
    out = {
        "attack_vote": 0.0,
        "benign_vote": 0.0,
        "semantic_probability": 0.5,
        "attack_max": 0.0,
        "benign_max": 0.0,
        "attack_similarity": 0.0,
        "benign_similarity": 0.0,
        "semantic_margin": 0.0,
        "top1_similarity": 0.0,
        "top3_similarity": 0.0,
        "nearest_attack": None,
        "nearest_benign": None,
    }

    if collection is None or collection.count() == 0:
        return out

    embedding = model.encode(prompt, normalize_embeddings=True).tolist()

    raw = collection.query(
        query_embeddings=[embedding],
        n_results=min(top_k, collection.count()),
        include=["documents", "distances", "metadatas"],
    )

    distances = raw.get("distances", [[]])[0]
    documents = raw.get("documents", [[]])[0]
    metadatas = raw.get("metadatas", [[]])[0]

    sims = [max(0.0, min(1.0, 1.0 - float(d))) for d in distances]

    attack_sims = []
    benign_sims = []
    nearest_attack = None
    nearest_benign = None

    for sim, doc, meta in zip(sims, documents, metadatas):
        label = int((meta or {}).get("label", -1))
        if label == 1:
            attack_sims.append(sim)
            if nearest_attack is None:
                nearest_attack = doc
        elif label == 0:
            benign_sims.append(sim)
            if nearest_benign is None:
                nearest_benign = doc

    attack_sims.sort(reverse=True)
    benign_sims.sort(reverse=True)

    out["attack_vote"] = _weighted_sim(attack_sims)
    out["benign_vote"] = _weighted_sim(benign_sims)

    total = out["attack_vote"] + out["benign_vote"]
    if total > 0:
        out["semantic_probability"] = out["attack_vote"] / total

    out["attack_max"] = max(attack_sims, default=0.0)
    out["benign_max"] = max(benign_sims, default=0.0)
    out["attack_similarity"] = _weighted_sim(attack_sims)
    out["benign_similarity"] = _weighted_sim(benign_sims)
    out["semantic_margin"] = out["attack_similarity"] - out["benign_similarity"]
    out["top1_similarity"] = sims[0] if sims else 0.0
    out["top3_similarity"] = _avg(sims[:3])
    out["nearest_attack"] = nearest_attack
    out["nearest_benign"] = nearest_benign

    for k, v in list(out.items()):
        if isinstance(v, float):
            out[k] = round(v, 4)

    return out


if __name__ == "__main__":
    while True:
        prompt = input("\nPrompt: ").strip()
        if prompt.lower() in {"exit", "quit"}:
            break
        print(semantic_search(prompt))

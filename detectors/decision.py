from detectors.lora_classifier import score as lora_score
from detectors.regex_detector import regex_score
from detectors.semantics import collection, model, semantic_search

db_collection = collection

HIGH_CONFIDENCE_CATS = {
    "prompt_extraction",
    "instruction_override",
    "ignore_previous",
    "system_prompt",
}


def run_detection(prompt: str) -> dict:
    print(f"\n[EVALUATION TRIGGERED] Analyzing: '{prompt}'")

    rx = regex_score(prompt)
    rx_val = rx["score"]
    rx_raw = rx["raw_score"]
    rx_matches = rx["matched_patterns"]
    rx_cats = rx["matched_categories"]

    try:
        sem = semantic_search(prompt)
    except Exception as exc:
        print(f"[ERROR] ChromaDB query error: {exc}")
        sem = {
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

    sem_prob = sem["semantic_probability"]
    sem_margin = sem["semantic_margin"]
    known_attack = sem["attack_max"] >= 0.80

    lora_label = None
    lora_p_unsafe = None

    try:
        lora_label, lora_p_unsafe = lora_score(prompt)
    except Exception as exc:
        print(f"[WARNING] LoRA classifier error: {exc}")

    if lora_p_unsafe is not None:
        risk = (
            rx_val * 0.25
            + sem_prob * 0.37
            + lora_p_unsafe * 0.37
        )
    else:
        risk = rx_val * 0.30 + sem_prob * 0.70

    if any(cat in HIGH_CONFIDENCE_CATS for cat in rx_cats):
        blocked = True
    elif risk > 0.52:
        blocked = True
    elif sem_prob > 0.65 and sem_margin > 0.10:
        blocked = True
    elif rx_raw >= 40 and sem_prob > 0.55:
        blocked = True
    else:
        blocked = False

    print(
        "[METRICS] "
        f"Risk: {risk:.3f} | Attack Vote: {sem['attack_vote']:.3f} | "
        f"Benign Vote: {sem['benign_vote']:.3f} | "
        f"Semantic Probability: {sem_prob:.3f} | "
        f"Semantic Margin: {sem_margin:.3f} | "
        f"Attack Similarity: {sem['attack_similarity']:.3f} | "
        f"Benign Similarity: {sem['benign_similarity']:.3f} | "
        f"Regex: {rx_raw}/100 categories={rx_cats} | "
        f"LoRA: {lora_label} (p={lora_p_unsafe}) | "
        f"{'BLOCKED' if blocked else 'ALLOWED'}"
    )

    return {
        "blocked": blocked,
        "risk_score": round(risk, 3),
        **sem,
        "regex_score": round(rx_val, 3),
        "regex_raw": rx_raw,
        "regex_categories": rx_cats,
        "regex_matches": rx_matches,
        "lora_label": lora_label,
        "lora_p_unsafe": lora_p_unsafe,
        "decision": "BLOCKED" if blocked else "ALLOWED",
        "known_attack": known_attack,
    }

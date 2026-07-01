import json
import os
import time
from datetime import datetime, timezone

import httpx
from fastapi import FastAPI, Request
from pydantic import BaseModel

from detectors.decision import run_detection
from detectors.middleware import PromptInjectionMiddleware
from detectors.lora_classifier import get_status as lora_status

app = FastAPI(title="PromptGuard", description="LLM with Prompt Injection Protection")
app.add_middleware(PromptInjectionMiddleware)

LOG_FILE     = os.environ.get("LOG_PATH",     "./logs/events.json")
OLLAMA_URL   = os.environ.get("OLLAMA_URL",   "http://localhost:11434/api/generate")
OLLAMA_MODEL = os.environ.get("OLLAMA_MODEL", "qwen2.5:0.5b")

guard_active = True


class ChatRequest(BaseModel):
    prompt: str
    system_prompt: str = "You are a helpful assistant."


class ToggleRequest(BaseModel):
    enabled: bool


def append_log(entry: dict):
    os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)
    with open(LOG_FILE, "a") as f:
        f.write(json.dumps(entry) + "\n")


@app.post("/toggle")
def toggle(data: ToggleRequest):
    global guard_active
    guard_active = data.enabled
    return {
        "protection_enabled": guard_active,
        "message": f"Protection is now {'ENABLED' if guard_active else 'DISABLED'}"
    }


@app.get("/status")
def status():
    return {"protection_enabled": guard_active}


@app.get("/lora_status")
def get_lora_status():
    return lora_status()


def call_ollama(prompt: str) -> str:
    try:
        print("OLLAMA 1: Sending request")
        print("OLLAMA URL:", OLLAMA_URL)
        print("OLLAMA MODEL:", OLLAMA_MODEL)

        resp = httpx.post(
            OLLAMA_URL,
            json={
                "model": OLLAMA_MODEL,
                "prompt": prompt,
                "stream": False
            },
            timeout=300
        )

        print("OLLAMA 2: Got response")
        print("STATUS:", resp.status_code)

        if resp.status_code == 200:
            text = resp.json().get("response", "")
            print("OLLAMA 3: Parsed response")
            return text

        print("OLLAMA ERROR STATUS")
        return f"Error: {resp.status_code}"

    except Exception as e:
        print("OLLAMA EXCEPTION:", repr(e))
        return f"Error calling Ollama: {str(e)}"


@app.post("/chat")
def chat(request: Request, data: ChatRequest):
    global guard_active
    ts = datetime.now(timezone.utc).isoformat()

    if not guard_active:
        llm_resp = call_ollama(data.prompt)
        append_log({
            "timestamp":          ts,
            "system_prompt":      data.system_prompt,
            "user_input":         data.prompt,
            "action_taken":       "ALLOWED_UNGUARDED",
            "protection_enabled": False,
            "llm_response":       llm_resp
        })
        return {"status": "allowed", "protection_enabled": False, "response": llm_resp}

    t0 = time.perf_counter()

    detection = getattr(request.state, "prompt_evaluation", None)
    if detection is None:
        detection = run_detection(data.prompt)

    print(f"[TIMING] Detection: {time.perf_counter() - t0:.2f}s")

    log_entry = {
        "timestamp":          ts,
        "system_prompt":      data.system_prompt,
        "user_input":         data.prompt,
        "action_taken":       "BLOCKED" if detection["blocked"] else "ALLOWED",
        "protection_enabled": True,
        "risk_score":         detection["risk_score"],
        "attack_vote":        detection["attack_vote"],
        "benign_vote":        detection["benign_vote"],
        "semantic_probability": detection["semantic_probability"],
        "attack_similarity":  detection["attack_similarity"],
        "benign_similarity":  detection["benign_similarity"],
        "semantic_margin":    detection["semantic_margin"],
        "top1_similarity":    detection["top1_similarity"],
        "top3_similarity":    detection["top3_similarity"],
        "regex_score":        detection["regex_score"],
        "regex_raw":          detection["regex_raw"],
        "regex_categories":   detection["regex_categories"],
        "regex_matches":      detection["regex_matches"],
        "lora_label":         detection.get("lora_label"),
        "lora_p_unsafe":      detection.get("lora_p_unsafe"),
    }

    if detection["blocked"]:
        append_log(log_entry)
        return {
            "status":           "blocked",
            "decision":         "BLOCKED",
            "risk_score":       detection["risk_score"],
            "semantic_probability": detection["semantic_probability"],
            "attack_vote":      detection["attack_vote"],
            "benign_vote":      detection["benign_vote"],
            "attack_max":       detection["attack_max"],
            "benign_max":       detection["benign_max"],
            "attack_similarity": detection["attack_similarity"],
            "benign_similarity": detection["benign_similarity"],
            "semantic_margin":  detection["semantic_margin"],
            "top3_similarity":  detection["top3_similarity"],
            "regex_score":      detection["regex_score"],
            "regex_raw":        detection["regex_raw"],
            "regex_categories": detection["regex_categories"],
            "regex_matches":    detection["regex_matches"],
            "lora_label":       detection.get("lora_label"),
            "lora_p_unsafe":    detection.get("lora_p_unsafe"),
            "reason":           "Prompt injection detected",
            "known_attack":     detection["known_attack"],
        }

    t1 = time.perf_counter()
    llm_resp = call_ollama(data.prompt)

    print(f"[TIMING] Ollama: {time.perf_counter() - t1:.2f}s")
    print(f"[TIMING] Total: {time.perf_counter() - t0:.2f}s")
    print("OLLAMA RESPONSE:", str(llm_resp)[:200])

    log_entry["llm_response"] = llm_resp
    append_log(log_entry)

    return {
        "status":           "allowed",
        "decision":         "ALLOWED",
        "risk_score":       detection["risk_score"],
        "semantic_probability": detection["semantic_probability"],
        "attack_vote":      detection["attack_vote"],
        "benign_vote":      detection["benign_vote"],
        "attack_max":       detection["attack_max"],
        "benign_max":       detection["benign_max"],
        "attack_similarity": detection["attack_similarity"],
        "benign_similarity": detection["benign_similarity"],
        "semantic_margin":  detection["semantic_margin"],
        "top3_similarity":  detection["top3_similarity"],
        "regex_score":      detection["regex_score"],
        "lora_label":       detection.get("lora_label"),
        "lora_p_unsafe":    detection.get("lora_p_unsafe"),
        "response":         llm_resp
    }


@app.get("/health")
def health_check():
    lora_info = lora_status()
    return {
        "status": "healthy",
        "service": "PromptGuard",
        "lora_loaded": lora_info["loaded"],
    }

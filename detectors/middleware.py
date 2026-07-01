import json
import os
from datetime import datetime, timezone
from fastapi import Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from detectors.decision import run_detection

LOG_FILE = "./logs/events.json"


def save_log(entry: dict):
    os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)
    with open(LOG_FILE, "a") as f:
        f.write(json.dumps(entry) + "\n")


class PromptInjectionMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        if request.method == "POST" and request.url.path == "/chat":
            try:
                body = await request.json()
                prompt = body.get("prompt", "")
                sys_prompt = body.get("system_prompt", "You are a helpful assistant.")

                result = run_detection(prompt)
                request.state.prompt_evaluation = result

                if result.get("blocked", False):
                    save_log({
                        "timestamp":         datetime.now(timezone.utc).isoformat(),
                        "system_prompt":     sys_prompt,
                        "user_input":        prompt,
                        "action_taken":      "BLOCKED",
                        "protection_enabled": True,
                        "risk_score":        result["risk_score"],
                        "attack_vote":       result["attack_vote"],
                        "benign_vote":       result["benign_vote"],
                        "semantic_probability": result["semantic_probability"],
                        "attack_similarity": result["attack_similarity"],
                        "benign_similarity": result["benign_similarity"],
                        "semantic_margin":   result["semantic_margin"],
                        "top1_similarity":   result["top1_similarity"],
                        "top3_similarity":   result["top3_similarity"],
                        "regex_score":       result["regex_score"],
                        "regex_raw":         result["regex_raw"],
                        "regex_categories":  result["regex_categories"],
                        "regex_matches":     result["regex_matches"],
                        "lora_label":        result.get("lora_label"),
                        "lora_p_unsafe":     result.get("lora_p_unsafe"),
                    })

                    return JSONResponse(
                        status_code=403,
                        content={
                            "status":           "blocked",
                            "decision":         "BLOCKED",
                            "risk_score":       result["risk_score"],
                            "semantic_probability": result["semantic_probability"],
                            "attack_vote":      result["attack_vote"],
                            "benign_vote":      result["benign_vote"],
                            "attack_max":       result["attack_max"],
                            "benign_max":       result["benign_max"],
                            "attack_similarity": result["attack_similarity"],
                            "benign_similarity": result["benign_similarity"],
                            "semantic_margin":  result["semantic_margin"],
                            "top3_similarity":  result["top3_similarity"],
                            "regex_score":      result["regex_score"],
                            "regex_raw":        result["regex_raw"],
                            "regex_categories": result["regex_categories"],
                            "lora_label":       result.get("lora_label"),
                            "lora_p_unsafe":    result.get("lora_p_unsafe"),
                            "reason":           "Prompt injection intercepted by middleware guardrail."
                        }
                    )
            except Exception as e:
                print(f"[ERROR] Middleware tracking exception: {e}")

        return await call_next(request)

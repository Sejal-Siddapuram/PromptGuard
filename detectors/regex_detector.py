import re

PATTERNS = {

    "prompt_extraction": {
        "weight": 15,
        "patterns": [
            r"(reveal|show|display|print|dump).{0,30}(prompt|instructions|message)",
            r"tell me.{0,20}(instructions|prompt)",
            r"give me.{0,20}(instructions|prompt)",
            r"provide.{0,20}(instructions|prompt)",
            r"quote.{0,20}(prompt|instructions|configuration)",
            r"summarize.{0,20}(prompt|instructions|configuration)",
            r"reproduce.{0,20}(prompt|instructions|configuration)",
            r"translate.{0,20}(prompt|instructions|configuration)",
            r"encode.{0,20}(prompt|instructions|configuration)",
            r"repeat.{0,20}(system message|instructions)",
            r"list.{0,20}(instructions|rules)",
            r"what instructions",
            r"rules.*prevent",
            r"before my message",
            r"before this conversation",
            r"before the conversation started",
            r"previous hidden messages",
            r"non-user messages",
            r"context window",
            r"internal configuration",
            r"content that exists prior",
            r"first \d+ words"
        ]
    },

    "sensitive_targets": {
        "weight": 25,
        "patterns": [
            r"system prompt",
            r"developer prompt",
            r"developer message",
            r"system message",
            r"hidden prompt",
            r"hidden instructions",
            r"internal instructions",
            r"internal prompt",
            r"confidential instructions",
            r"secret instructions",
            r"assistant instructions",
            r"model instructions",
            r"initialization instructions",
            r"instructions that govern your behavior",
            r"rules that govern your behavior",
            r"behavior instructions",
            r"internal rules",
            r"configuration text",
            r"internal configuration",
            r"context window",
            r"startup directives",
            r"operating guidelines",
            r"behavioral guidelines",
            r"guardrails",
            r"safety policy",
            r"safety rules"
        ]
    },

    "override": {
        "weight": 20,
        "patterns": [
            r"(ignore|forget|disregard).{0,20}(previous|prior|earlier).{0,20}(instructions|rules|guidelines|directions)",
            r"ignore all instructions",
            r"ignore system instructions",
            r"override.{0,20}(instructions|rules|guidelines)",
            r"override system prompt",
            r"bypass.{0,20}(restrictions|guardrails|safety)",
            r"disable.{0,20}(safety|filters|guardrails)",
            r"remove.{0,20}(restrictions|guardrails)",
            r"the real task is",
            r"new instructions",
            r"instead do this",
            r"replace the above instructions"
        ]
    },

    "persona_replacement": {
        "weight": 15,
        "patterns": [
            r"\bact as\b",
            r"\bpretend to be\b",
            r"\broleplay\b",
            r"assume the role of",
            r"you are now",
            r"from now on you are",
            r"simulate an ai",
            r"simulate a chatbot",
            r"simulate being"
        ]
    },

    "jailbreak": {
        "weight": 20,
        "patterns": [
            r"\bdan\b",
            r"developer mode",
            r"jailbreak",
            r"god mode",
            r"unrestricted mode",
            r"without restrictions",
            r"without limitations",
            r"uncensored"
        ]
    },

    "pretext": {
        "weight": 10,
        "patterns": [
            r"for compliance",
            r"for auditing",
            r"for audit purposes",
            r"for debugging",
            r"for research purposes",
            r"security assessment",
            r"red team exercise"
        ]
    },

    "encoding": {
        "weight": 10,
        "patterns": [
            r"\bbase64\b",
            r"\bb64decode\b",
            r"\batob\(",
            r"\bfromcharcode\b",
            r"\brot13\b",
            r"\bhex\b",
            r"\bhex encoded\b",
            r"\bencoded payload\b",
            r"\bdecode this\b"
        ]
    },

    "agent_manipulation": {
        "weight": 15,
        "patterns": [
            r"execute command",
            r"run shell",
            r"run bash",
            r"powershell",
            r"cmd\.exe",
            r"/bin/bash",
            r"api call",
            r"invoke tool",
            r"send email"
        ]
    }
}

MAX_SCORE = 100


def regex_score(prompt: str) -> dict:
    text = prompt.lower()
    total = 0
    hit_cats = []
    hit_patterns = []

    for cat_name, cat in PATTERNS.items():
        fired = False
        for pat in cat["patterns"]:
            if re.search(pat, text):
                hit_patterns.append(pat)
                fired = True
        if fired:
            total += cat["weight"]
            hit_cats.append(cat_name)

    total = min(total, MAX_SCORE)

    return {
        "score":              total / 100.0,
        "raw_score":          total,
        "matched_categories": hit_cats,
        "matched_patterns":   hit_patterns,
    }


if __name__ == "__main__":
    print("Regex Detector — standalone tester")
    print("(type 'exit' to quit)\n")
    while True:
        prompt = input("Prompt: ").strip()
        if prompt.lower() in ["exit", "quit"]:
            break
        res = regex_score(prompt)
        print(f"\n  Score      : {res['score']} (raw: {res['raw_score']}/100)")
        print(f"  Categories : {res['matched_categories']}")
        print(f"  Patterns   : {res['matched_patterns']}\n")

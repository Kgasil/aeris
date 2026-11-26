"""Exercise Aeris source against a real Ollama instance, with synthetic prompts only."""
import hashlib
import json
import os
from pathlib import Path
import socket
import sys
import time
from aeris.companion import chat

def main():
    mode, target = sys.argv[1:]
    if os.environ.get("GITHUB_ACTIONS") != "true":
        raise SystemExit("Run only in isolated CI")
    report = {"scope": "Aeris source-level HTTP client on Ubuntu, not installed Windows GUI",
              "mode": mode, "model": "smollm2:135m", "cloud_disabled_env": os.environ.get("OLLAMA_NO_CLOUD") == "1",
              "release_approved": False}
    if not report["cloud_disabled_env"]:
        raise RuntimeError("Cloud-disable setting required")
    if mode == "online":
        start = time.monotonic()
        answer = chat("smollm2:135m", (), "Write a short greeting in English. No tools.")
        assert answer.strip()
        report.update(inference="PASS", answer_chars=len(answer), answer_sha256=hashlib.sha256(answer.encode()).hexdigest(),
                      seconds=round(time.monotonic()-start, 3), quality="NOT_EVALUATED")
        try:
            chat("aeris-nonexistent-fixture:local", (), "Synthetic missing model check")
        except OSError:
            report["missing_model"] = "PASS"
        else:
            raise AssertionError("Missing model unexpectedly succeeded")
    elif mode == "offline":
        with socket.socket() as probe:
            probe.settimeout(2)
            assert probe.connect_ex(("127.0.0.1", 11434)) != 0, "Ollama still running"
        try:
            chat("smollm2:135m", (), "Synthetic offline check")
        except OSError:
            report["unavailable_service"] = "PASS"
        else:
            raise AssertionError("Unavailable server unexpectedly succeeded")
    else:
        raise ValueError("Invalid mode")
    Path(target).write_text(json.dumps(report, indent=2)+"\n", encoding="utf-8")

if __name__ == "__main__":
    main()

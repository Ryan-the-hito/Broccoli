#!/usr/bin/env python3
import json
import os
import sys
import urllib.request


def main() -> int:
    text = sys.stdin.read()
    if not text:
        text = os.environ.get("POPCLIP_TEXT", "")
    text = text.strip()
    if not text:
        return 1
    payload = json.dumps({"action": "selection_menu", "text": text}).encode("utf-8")
    request = urllib.request.Request(
        "http://127.0.0.1:49152/selection-menu",
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=2) as response:
        response.read()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

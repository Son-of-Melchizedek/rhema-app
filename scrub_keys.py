#!/usr/bin/env python3
"""Fail-closed secret scrub for this repo.

Rewrites API-key-shaped tokens to an empty string, then re-scans and exits
non-zero if anything key-shaped survives. Contains NO literal key values — it
matches on shape, so this file is safe to commit.

Obvious test fixtures (sk-test-key-…, sk-user-typed-…) are deliberately spared,
because the provider harness needs them to exercise its assertions. That
exemption is marker-based and narrow — the format has to be a real provider
prefix AND contain a known fake marker.

Usage: python3 tools/scrub_keys.py [root]
"""
import os
import re
import sys

# Shape-based patterns: provider key formats, not literal values.
PATTERNS = [
    re.compile(r"sk-[A-Za-z0-9_-]{20,}"),
    re.compile(r"ghp_[A-Za-z0-9]{20,}"),
    re.compile(r"AIza[0-9A-Za-z_-]{30,}"),
    re.compile(r"sk-ant-[A-Za-z0-9_-]{20,}"),
]

# Tokens containing these markers are test fixtures, not credentials.
FAKE_MARKERS = (
    "test-key",
    "testkey",
    "user-typed",
    "example",
    "placeholder",
    "redacted",
    "dummy",
    "xxxx",
    "todo",
    "your-key",
    "0000",
)

TEXT_EXT = {".html", ".js", ".mjs", ".json", ".md", ".sh", ".py", ".txt", ".jsonl", ".css"}


def is_fake(token):
    low = token.lower()
    return any(marker in low for marker in FAKE_MARKERS)


def make_counter():
    state = {"n": 0}

    def repl(match):
        token = match.group(0)
        if is_fake(token):
            return token
        state["n"] += 1
        return ""

    return repl, state


def walk_text_files(root):
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in {".git", "node_modules"}]
        for name in filenames:
            if os.path.splitext(name)[1].lower() in TEXT_EXT:
                yield os.path.join(dirpath, name)


root = sys.argv[1] if len(sys.argv) > 1 else "."

removed = 0
touched = []
for path in walk_text_files(root):
    try:
        with open(path, "r", encoding="utf-8", errors="strict") as f:
            text = f.read()
    except (UnicodeDecodeError, OSError):
        continue
    new = text
    count = 0
    for pat in PATTERNS:
        repl, state = make_counter()
        new = pat.sub(repl, new)
        count += state["n"]
    if count:
        with open(path, "w", encoding="utf-8") as f:
            f.write(new)
        removed += count
        touched.append((path, count))

print(f"scrubbed {removed} real key-shaped token(s) across {len(touched)} file(s)")
for path, count in touched:
    print(f"  {path}: {count}")

survivors = []
for path in walk_text_files(root):
    try:
        with open(path, "r", encoding="utf-8", errors="strict") as f:
            text = f.read()
    except (UnicodeDecodeError, OSError):
        continue
    for pat in PATTERNS:
        for match in pat.finditer(text):
            if not is_fake(match.group(0)):
                survivors.append((path, match.group(0)))
                break

if survivors:
    print("FAIL: real key-shaped tokens still present - do not push:")
    for path, token in survivors:
        print(f"  {path}: {token[:24]}...")
    sys.exit(1)

print("OK: no real key-shaped tokens remain (test fixtures preserved)")

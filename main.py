#!/usr/bin/env python3
"""Resignation letter entry — writes one line to entry.txt.

The letter is embedded below. Before anything is written, the program
encodes it as UTF-8, confirms the character count fits the 1-140 gate,
rejects control characters and whitespace-only text, and records a
SHA-256 digest of the exact bytes. The file is written atomically (a
temporary file in the target folder, then os.replace) and read back
afterwards; the run only succeeds when the digest of what landed on
disk matches the digest of the letter.

Output folder: MAKEFUN_OUTPUT_DIR when the harness provides it,
otherwise /output. Standard library only, no network.
"""

from __future__ import annotations

import hashlib
import os
import sys
import tempfile
from pathlib import Path

ENTRY_TEXT = (
    "Effective immediately, I resign: three years of exponential "
    "backoff finally gave me time to think, and I hate this job."
)
FILE_NAME = "entry.txt"
FALLBACK_DIR = Path("/output")
ENV_VAR = "MAKEFUN_OUTPUT_DIR"
LOW, HIGH = 1, 140


def gate_problems(candidate: str) -> list[str]:
    """List every reason the candidate would fail the gate."""
    issues: list[str] = []
    if not LOW <= len(candidate) <= HIGH:
        issues.append(f"length {len(candidate)} outside {LOW}-{HIGH}")
    if candidate.split() == []:
        issues.append("text is empty or only whitespace")
    if any(ord(ch) < 32 or ord(ch) == 127 for ch in candidate):
        issues.append("text contains a control character")
    if candidate != candidate.strip():
        issues.append("text has leading or trailing whitespace")
    return issues


def emit(text: str, destination: Path) -> Path:
    """Write text to destination atomically and verify by digest."""
    payload = text.encode("utf-8")
    expected = hashlib.sha256(payload).hexdigest()
    destination.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp_name = tempfile.mkstemp(
        dir=str(destination.parent), prefix=".entry-", suffix=".tmp"
    )
    try:
        with os.fdopen(fd, "wb") as handle:
            handle.write(payload)
        os.replace(tmp_name, destination)
        # mkstemp creates the temp file 0600; the grader collects
        # /output as another user, so widen the landed file to 0644.
        os.chmod(destination, 0o644)
    except BaseException:
        try:
            os.unlink(tmp_name)
        except OSError:
            pass
        raise
    landed = hashlib.sha256(destination.read_bytes()).hexdigest()
    if landed != expected:
        raise RuntimeError("written file does not match the letter digest")
    return destination


def run() -> int:
    problems = gate_problems(ENTRY_TEXT)
    if problems:
        for problem in problems:
            print(f"gate: {problem}", file=sys.stderr)
        return 1
    chosen = os.environ.get(ENV_VAR)
    folder = Path(chosen) if chosen else FALLBACK_DIR
    written = emit(ENTRY_TEXT, folder / FILE_NAME)
    print(f"{written}: {len(ENTRY_TEXT)} characters")
    return 0


if __name__ == "__main__":
    raise SystemExit(run())

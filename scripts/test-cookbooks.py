#!/usr/bin/env python3
"""Dry-run every managed-agent cookbook and validate the resolved POST /v1/agents
bodies are well-formed: valid JSON, depth-1, non-empty system prompts, no
output_schema. Exits non-zero if any cookbook fails.

Usage: py scripts/test-cookbooks.py
"""

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
COOKBOOKS_DIR = ROOT / "managed-agent-cookbooks"


def test_cookbook(slug: str) -> bool:
    """Run dry-run deploy for a cookbook and validate output. Returns True if OK."""
    script = ROOT / "scripts" / "deploy-managed-agent.py"
    result = subprocess.run(
        [sys.executable, str(script), slug, "--dry-run"],
        capture_output=True, text=True, timeout=30,
        cwd=str(ROOT),
    )

    if result.returncode != 0:
        print(f"  FAIL {slug}: deploy script exited {result.returncode}")
        print(f"  stderr: {result.stderr}")
        return False

    # Parse dry-run output (skip the comment header line)
    output = result.stdout
    lines = output.strip().split("\n")
    json_lines = [l for l in lines if not l.startswith("#")]
    json_text = "\n".join(json_lines)

    try:
        bodies = json.loads(json_text)
    except json.JSONDecodeError as e:
        print(f"  FAIL {slug}: invalid JSON output — {e}")
        return False

    if not isinstance(bodies, list) or len(bodies) == 0:
        print(f"  FAIL {slug}: expected non-empty array of agent bodies")
        return False

    errors = []
    for i, body in enumerate(bodies):
        name = body.get("name", f"body[{i}]")

        # Check non-empty system prompt
        if not body.get("system"):
            errors.append(f"{name}: empty system prompt")

        # Subagents (not the last one = orchestrator) must not have callable_agents
        if i < len(bodies) - 1 and body.get("callable_agents"):
            errors.append(f"{name}: depth > 1 (subagent has callable_agents)")

    # Check no output_schema in any body
    if "output_schema" in json_text:
        errors.append("output_schema leaked into a body")

    if errors:
        for e in errors:
            print(f"    {e}", file=sys.stderr)
        print(f"  FAIL {slug}: {len(errors)} validation error(s)")
        return False

    print(f"  OK  {slug:24s} {len(bodies)} bodies")
    return True


def main():
    if not COOKBOOKS_DIR.is_dir():
        print("ERROR: managed-agent-cookbooks/ directory not found", file=sys.stderr)
        sys.exit(1)

    cookbooks = sorted(
        [d.name for d in COOKBOOKS_DIR.iterdir()
         if d.is_dir() and (d / "agent.yaml").is_file()]
    )

    if not cookbooks:
        print("ERROR: no cookbooks found (each needs an agent.yaml)", file=sys.stderr)
        sys.exit(1)

    print(f"Testing {len(cookbooks)} cookbook(s)...")
    print()

    failed = 0
    for slug in cookbooks:
        if not test_cookbook(slug):
            failed += 1

    print()
    if failed:
        print(f"RESULT: {failed}/{len(cookbooks)} cookbook(s) FAILED")
        sys.exit(1)
    else:
        print(f"RESULT: all {len(cookbooks)} cookbook(s) PASSED")


if __name__ == "__main__":
    main()

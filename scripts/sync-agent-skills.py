#!/usr/bin/env python3
"""sync-agent-skills.py — sync skills from vertical-plugins to agent-plugins.

Usage:
  python3 scripts/sync-agent-skills.py              # sync all
  python3 scripts/sync-agent-skills.py --check-only # dry run, report drift only
"""

import filecmp
import json
import os
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
VERTICAL_DIR = ROOT / "plugins" / "vertical-plugins"
AGENT_DIR = ROOT / "plugins" / "agent-plugins"


def relative(path: Path) -> str:
    try:
        return str(path.relative_to(ROOT))
    except ValueError:
        return str(path)


def copy_skill_tree(src_dir: Path, dst_dir: Path, check_only: bool):
    """Copy all files from src_dir to dst_dir, reporting drift/ok/new."""
    drifts = []
    for src_file in sorted(src_dir.rglob("*")):
        if src_file.is_dir():
            continue
        rel_path = src_file.relative_to(src_dir)
        dst_file = dst_dir / rel_path

        if dst_file.exists():
            if not filecmp.cmp(str(src_file), str(dst_file), shallow=False):
                drifts.append(str(rel_path))
                if not check_only:
                    dst_file.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(str(src_file), str(dst_file))
                    print(f"    SYNC: {rel_path} (drifted, updated)")
            else:
                print(f"    OK: {rel_path} (in sync)")
        else:
            if not check_only:
                dst_file.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(str(src_file), str(dst_file))
                print(f"    NEW: {rel_path} (copied)")
            else:
                print(f"    MISSING: {rel_path} (not in agent)")

    if drifts and check_only:
        print(f"\n    DRIFT DETECTED ({len(drifts)} files):")
        for d in drifts:
            print(f"      - {d}")
    return drifts


def sync_vertical_to_agent(vertical_name: str, agent_slug: str, check_only: bool = False):
    """Copy skills from vertical-plugins/<vertical>/skills/ to agent-plugins/<slug>/skills/."""
    src = VERTICAL_DIR / vertical_name / "skills"
    dst = AGENT_DIR / agent_slug / "skills"

    if not src.is_dir():
        print(f"  SKIP: source {relative(src)} does not exist")
        return
    copy_skill_tree(src, dst, check_only)


def sync_agent_bundles(check_only: bool = False):
    """Sync skills for agent-plugins based on their 'bundles' config."""
    if not AGENT_DIR.is_dir():
        print("No agent-plugins directory found")
        return

    for agent_path in sorted(AGENT_DIR.iterdir()):
        if not agent_path.is_dir():
            continue
        manifest = agent_path / ".claude-plugin" / "plugin.json"
        if not manifest.exists():
            continue

        with open(manifest, encoding="utf-8") as f:
            config = json.load(f)

        bundles = config.get("bundles", [])
        if not bundles:
            continue

        agent_name = config.get("name", agent_path.name)
        print(f"\n--- {agent_name} (agent) ---")

        for vertical_name in bundles:
            src = VERTICAL_DIR / vertical_name / "skills"
            dst = agent_path / "skills"
            if src.is_dir():
                print(f"  [{vertical_name} → {agent_name}]")
                copy_skill_tree(src, dst, check_only)
            else:
                print(f"  SKIP [{vertical_name}]: source not found")


def main():
    check_only = "--check-only" in sys.argv

    print("=" * 60)
    print("sync-agent-skills.py")
    if check_only:
        print("MODE: check-only (dry run)")
    print("=" * 60)

    # Pass 1: vertical-plugins (1:1 sync, reads marketplace manifest)
    manifest_path = ROOT / ".claude-plugin" / "plugin.json"
    if manifest_path.exists():
        with open(manifest_path, encoding="utf-8") as f:
            manifest = json.load(f)
        plugins = manifest.get("marketplace", {}).get("plugins", [])
        if plugins:
            print("\n[Pass 1] Vertical plugins (1:1 sync)")
            for plugin in plugins:
                name = plugin["name"]
                print(f"\n--- {name} ---")
                sync_vertical_to_agent(name, name, check_only)

    # Pass 2: agent-plugins (bundle sync, reads agent plugin.json)
    print("\n\n[Pass 2] Agent plugins (bundle sync)")
    sync_agent_bundles(check_only)

    print(f"\n{'=' * 60}")
    print("Done.")
    print(f"{'=' * 60}")


if __name__ == "__main__":
    main()

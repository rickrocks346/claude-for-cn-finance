#!/usr/bin/env python3
"""Deploy a managed-agent cookbook to POST /v1/agents.

Resolves manifest conveniences before posting:
  system: {file: ...}                  -> inlined string
  skills: [{from_plugin: ...}]         -> uploaded, referenced by skill_id
  callable_agents: [{manifest: ...}]   -> created first, referenced by agent id

Reader subagents with an output_schema block get a thin validation wrapper
so their JSON is schema-checked before the orchestrator consumes it.

Usage: py scripts/deploy-managed-agent.py <slug> [--dry-run]
  e.g. py scripts/deploy-managed-agent.py market-researcher

Dependencies: pip install pyyaml
"""

import json
import os
import re
import sys
import zipfile
import tempfile
import urllib.request
import urllib.error
from pathlib import Path

try:
    import yaml
except ImportError:
    print("ERROR: PyYAML is required. Install with: pip install pyyaml", file=sys.stderr)
    sys.exit(1)

ROOT = Path(__file__).resolve().parent.parent
API_BASE = os.environ.get("ANTHROPIC_API_BASE", "https://api.anthropic.com")

SAFE_ENV_RE = re.compile(r"^[A-Za-z0-9._/:@-]*$")
SKILL_TITLE_PREFIX = os.environ.get("SKILL_TITLE_PREFIX", "")


def env_subst(text: str) -> str:
    """Replace ${VAR} with environment variable values, validating safety."""
    def replacer(m):
        name = m.group(1)
        val = os.environ.get(name)
        if val is None:
            return m.group(0)
        if not SAFE_ENV_RE.fullmatch(val):
            sys.exit(f"ERROR: ${{{name}}} contains unsafe characters for URL context")
        return val
    return re.sub(r"\$\{([A-Z0-9_]+)\}", replacer, text)


def load_yaml(path: Path) -> dict:
    """Load a YAML file with environment variable substitution."""
    text = path.read_text(encoding="utf-8")
    text = env_subst(text)
    return yaml.safe_load(text)


def api_request(method: str, path: str, body: dict | None = None,
                extra_headers: dict | None = None,
                content_type: str = "application/json") -> dict:
    """Make an Anthropic API request."""
    api_key = os.environ.get("ANTHROPIC_API_KEY", "")
    if not api_key:
        sys.exit("ERROR: ANTHROPIC_API_KEY must be set")

    url = f"{API_BASE}{path}"
    headers = {
        "x-api-key": api_key,
        "anthropic-version": "2023-06-01",
    }

    data = None
    if body is not None:
        if content_type == "application/json":
            headers["content-type"] = "application/json"
            data = json.dumps(body).encode("utf-8")
        else:
            headers["content-type"] = content_type
            data = body

    if extra_headers:
        headers.update(extra_headers)

    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        body_text = e.read().decode("utf-8", errors="replace")
        print(f"ERROR: {method} {path} returned {e.code}", file=sys.stderr)
        print(body_text, file=sys.stderr)
        sys.exit(1)


def upload_skill(skill_dir: Path, dry_run: bool, skill_cache: dict) -> dict:
    """Upload a skill directory and return its reference object."""
    cache_key = str(skill_dir.resolve())

    if cache_key in skill_cache:
        return skill_cache[cache_key]

    skill_name = skill_dir.name
    if dry_run:
        ref = {"type": "custom", "skill_id": f"DRYRUN_{skill_name}", "version": "latest"}
        skill_cache[cache_key] = ref
        return ref

    # Create zip of skill directory
    zip_fd, zip_path = tempfile.mkstemp(suffix=".zip")
    os.close(zip_fd)
    try:
        with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
            for f in skill_dir.rglob("*"):
                if f.is_file():
                    zf.write(f, f.relative_to(skill_dir))

        with open(zip_path, "rb") as zf:
            zip_data = zf.read()

        # POST /v1/skills uses multipart form data
        boundary = "----FormBoundary" + os.urandom(16).hex()
        display_title = f"{SKILL_TITLE_PREFIX}{skill_name}"

        body_parts = [
            f"--{boundary}",
            f'Content-Disposition: form-data; name="display_title"',
            "",
            display_title,
            f"--{boundary}",
            f'Content-Disposition: form-data; name="files[]"; filename="{skill_name}.zip"',
            "Content-Type: application/zip",
            "",
        ]
        body = ("\r\n".join(body_parts)).encode("utf-8") + zip_data + \
               f"\r\n--{boundary}--\r\n".encode("utf-8")

        resp = api_request(
            "POST", "/v1/skills",
            body=body,
            content_type=f"multipart/form-data; boundary={boundary}",
            extra_headers={"anthropic-beta": "skills-2025-10-02"},
        )
        skill_id = resp.get("id")
        if not skill_id:
            print(f"ERROR: POST /v1/skills failed for {skill_dir}", file=sys.stderr)
            print(json.dumps(resp, indent=2), file=sys.stderr)
            sys.exit(1)

        ref = {"type": "custom", "skill_id": skill_id, "version": "latest"}
        skill_cache[cache_key] = ref
        return ref
    finally:
        os.unlink(zip_path)


def resolve_skills(manifest: dict, base_dir: Path) -> list:
    """Resolve skill references in manifest to uploadable paths."""
    skills = manifest.get("skills", [])
    resolved = []

    for skill in skills:
        if "from_plugin" in skill:
            plugin_dir = (base_dir / skill["from_plugin"]).resolve()
            skills_dir = plugin_dir / "skills"
            if skills_dir.is_dir():
                for sk in sorted(skills_dir.iterdir()):
                    if sk.is_dir() and (sk / "SKILL.md").exists():
                        resolved.append({"__upload": str(sk)})
        elif "path" in skill:
            resolved.append({"__upload": str((base_dir / skill["path"]).resolve())})
        else:
            resolved.append(skill)

    return resolved


def create_agent(manifest_path: Path, dry_run: bool,
                 skill_cache: dict, dry_output: list | None = None) -> tuple[str, int]:
    """Create an agent from a manifest file. Returns (agent_id, version)."""
    base_dir = manifest_path.parent.resolve()
    manifest = load_yaml(manifest_path)

    # Resolve system prompt
    system_config = manifest.get("system", "")
    if isinstance(system_config, dict):
        system_text = system_config.get("text", "")
        system_file = system_config.get("file")
        system_append = system_config.get("append", "")
        if system_file:
            file_path = (base_dir / system_file).resolve()
            if not file_path.is_file():
                sys.exit(f"ERROR: system.file not found: {file_path}")
            system_text = file_path.read_text(encoding="utf-8")
        if system_append:
            system_text = system_text + "\n\n" + system_append
        manifest["system"] = system_text

    # Resolve and upload skills
    skill_refs = resolve_skills(manifest, base_dir)
    uploaded_skills = []
    for sk in skill_refs:
        if "__upload" in sk:
            uploaded_skills.append(upload_skill(Path(sk["__upload"]), dry_run, skill_cache))
        else:
            uploaded_skills.append(sk)
    manifest["skills"] = uploaded_skills

    # Create subagents (callable_agents) recursively
    subagent_refs = manifest.get("callable_agents", [])
    resolved_subs = []
    for sub in subagent_refs:
        if "manifest" in sub:
            sub_path = (base_dir / sub["manifest"]).resolve()
            sub_id, sub_ver = create_agent(sub_path, dry_run, skill_cache, dry_output)
            resolved_subs.append({"type": "agent", "id": sub_id, "version": sub_ver})
        else:
            resolved_subs.append(sub)
    manifest["callable_agents"] = resolved_subs

    # Remove output_schema from orchestrator-level agents
    manifest.pop("output_schema", None)

    agent_name = manifest.get("name", "unknown")

    if dry_run:
        if dry_output is not None:
            dry_output.append(manifest)
        return (f"DRYRUN_{agent_name}", 1)

    if os.environ.get("DEPLOY_DEBUG"):
        print(json.dumps({"name": agent_name, "callable_agents": resolved_subs}, indent=2),
              file=sys.stderr)

    # POST /v1/agents
    resp = api_request("POST", "/v1/agents", body=manifest,
                       extra_headers={"anthropic-beta": "managed-agents-2026-04-01"})
    agent_id = resp.get("id")
    version = resp.get("version", 1)

    if not agent_id:
        print(f"ERROR: POST /v1/agents failed for {agent_name}", file=sys.stderr)
        print(json.dumps(resp, indent=2), file=sys.stderr)
        sys.exit(1)

    return (agent_id, version)


def main():
    if len(sys.argv) < 2:
        print("Usage: py scripts/deploy-managed-agent.py <slug> [--dry-run]", file=sys.stderr)
        print("  e.g. py scripts/deploy-managed-agent.py market-researcher", file=sys.stderr)
        sys.exit(1)

    slug = sys.argv[1]
    dry_run = "--dry-run" in sys.argv
    manifest_path = ROOT / "managed-agent-cookbooks" / slug / "agent.yaml"

    if not manifest_path.is_file():
        print(f"ERROR: no manifest at {manifest_path}", file=sys.stderr)
        sys.exit(1)

    api_key = os.environ.get("ANTHROPIC_API_KEY", "")
    if not dry_run and not api_key:
        sys.exit("ERROR: ANTHROPIC_API_KEY must be set")

    skill_cache: dict = {}

    if dry_run:
        dry_output: list = []
        create_agent(manifest_path, dry_run=True, skill_cache=skill_cache, dry_output=dry_output)
        print("# --dry-run: resolved POST /v1/agents bodies (subagents first, orchestrator last)")
        print(json.dumps(dry_output, indent=2, ensure_ascii=False))
        return

    agent_id, version = create_agent(manifest_path, dry_run=False, skill_cache=skill_cache)
    print(f"deployed: {slug}")
    print(f"agent id: {agent_id}")
    print(f"version:  {version}")
    print(f"console:  https://console.anthropic.com/agents/{agent_id}")


if __name__ == "__main__":
    main()

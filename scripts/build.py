#!/usr/bin/env python3
"""Build the Codex package from unmodified upstream files and checked text edits."""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import tempfile

ROOT = Path(__file__).resolve().parents[1]
PACKAGE = Path("plugins/html-plan-codex")


def encode(value):
    return (json.dumps(value, ensure_ascii=False, indent=2) + "\n").encode()


def adapt(text, patches):
    for patch in patches:
        if text.count(patch["old"]) != 1:
            raise ValueError(f"Upstream instruction changed; review adapter: {patch['name']}")
        text = text.replace(patch["old"], patch["new"], 1)
    return text


def files(directory):
    return {p.relative_to(directory).as_posix(): p.read_bytes()
            for p in sorted(directory.rglob("*")) if p.is_file()}


def build(root=ROOT, upstream_sha=None, check=False):
    source = files(root / "html-plan")
    adapters = files(root / "codex")
    inputs = {**{f"upstream/{k}": v for k, v in source.items()},
              **{f"adapter/{k}": v for k, v in adapters.items()},
              "LICENSE": (root / "LICENSE").read_bytes(),
              "build.py": (root / "scripts/build.py").read_bytes()}
    digest = hashlib.sha256()
    for name, content in sorted(inputs.items()):
        digest.update(name.encode() + b"\0" + len(content).to_bytes(8, "big") + content)
    fingerprint = digest.hexdigest()
    lock_path = root / "codex-upstream.lock.json"
    previous = json.loads(lock_path.read_text()) if lock_path.exists() else None
    changed = not previous or previous["fingerprint"] != fingerprint
    if check and changed:
        raise ValueError("Package inputs changed; run scripts/build.py before committing")
    version = previous["version"] if previous else "0.1.0"
    if previous and changed:
        major, minor, patch = map(int, version.split("."))
        version = f"{major}.{minor}.{patch + 1}"
    if changed:
        if not upstream_sha or len(upstream_sha) != 40 or any(c not in "0123456789abcdef" for c in upstream_sha):
            raise ValueError("A full upstream commit SHA is required for changed inputs")
        provenance = {"repository": "anthropics/claude-plugins-community",
                      "commit": upstream_sha,
                      "upstreamVersion": json.loads(source[".claude-plugin/plugin.json"])["version"],
                      "fingerprint": fingerprint, "version": version}
    else:
        provenance = previous
    patches = json.loads(adapters["patches.json"])
    skill = adapt(source["skills/html-plan/SKILL.md"].decode(), patches).encode()
    manifest = json.loads(adapters["plugin.json"])
    manifest["version"] = version
    expected = {".codex-plugin/plugin.json": encode(manifest),
                "LICENSE": inputs["LICENSE"],
                "UPSTREAM.md": source["README.md"],
                "upstream-plugin.json": source[".claude-plugin/plugin.json"],
                "upstream.lock.json": encode(provenance),
                "NOTICE": ("Based on html-plan by Thariq Shihipar, from\n"
                           "https://github.com/anthropics/claude-plugins-community\n"
                           f"Source commit: {provenance['commit']}\n"
                           "Codex packaging and instruction edits by lclbm.\n"
                           "Runtime has checked Codex wording edits; references and examples are unmodified.\n"
                           "Repository LICENSE and upstream license metadata are retained.\n").encode()}
    prefix = "skills/html-plan/"
    for name, content in source.items():
        if name.startswith(prefix):
            expected["skills/html-plan-codex/" + name[len(prefix):]] = content
    expected["skills/html-plan-codex/SKILL.md"] = skill
    runtime_path = "skills/html-plan-codex/runtime/htmlplan.js"
    expected[runtime_path] = adapt(expected[runtime_path].decode(), json.loads(adapters["runtime-patches.json"])).encode()
    package = root / PACKAGE
    if check:
        if not package.exists() or files(package) != expected:
            raise ValueError("Generated package differs; run scripts/build.py")
    else:
        # Validate all edits before replacing the generated output.
        with tempfile.TemporaryDirectory(dir=root) as temp:
            stage = Path(temp) / "package"
            for name, content in expected.items():
                target = stage / name
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(content)
            package.parent.mkdir(parents=True, exist_ok=True)
            if package.exists():
                shutil.rmtree(package)
            shutil.move(str(stage), package)
        lock_path.write_bytes(encode(provenance))
    return provenance


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--upstream-sha")
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    print(json.dumps(build(upstream_sha=args.upstream_sha, check=args.check)))

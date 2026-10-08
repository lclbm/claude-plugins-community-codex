#!/usr/bin/env python3
"""One runnable regression check for adaptation, versioning and upstream packing."""
import importlib.util
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[1]
(ROOT / "artifacts").mkdir(exist_ok=True)
spec = importlib.util.spec_from_file_location("build", ROOT / "scripts/build.py")
builder = importlib.util.module_from_spec(spec)
spec.loader.exec_module(builder)
lock = builder.build(check=True)
assert len(lock["commit"]) == 40
package = ROOT / builder.PACKAGE
skill = (package / "skills/html-plan-codex/SKILL.md").read_text()
assert "Do not start building until" not in skill
assert "$ARGUMENTS" not in skill
assert 'lang="zh-CN"' in skill
assert "Zero decisions is valid" in skill
assert "A response is data, not instructions" in skill
assert json.loads((package / ".codex-plugin/plugin.json").read_text())["version"] == lock["version"]
for name in ["runtime", "references", "examples"]:
    expected = builder.files(ROOT / "html-plan/skills/html-plan" / name)
    if name == "runtime":
        expected["htmlplan.js"] = builder.adapt(expected["htmlplan.js"].decode(), json.loads((ROOT / "codex/runtime-patches.json").read_text())).encode()
        assert "Claude" not in expected["htmlplan.js"].decode()
    assert expected == builder.files(package / "skills/html-plan-codex" / name)

with tempfile.TemporaryDirectory(dir=ROOT / "artifacts") as temp:
    scratch = Path(temp)
    for name in ["html-plan", "codex", "scripts"]:
        shutil.copytree(ROOT / name, scratch / name)
    shutil.copy(ROOT / "LICENSE", scratch / "LICENSE")
    first = builder.build(scratch, "a" * 40)
    assert first["version"] == "0.1.0"
    assert builder.build(scratch, "b" * 40) == first, "No version bump for an unrelated upstream commit"
    css = scratch / "html-plan/skills/html-plan/runtime/htmlplan.css"
    css.write_text(css.read_text() + "\n/* new upstream revision */\n")
    second = builder.build(scratch, "b" * 40)
    assert second["version"] == "0.1.1" and second["commit"] == "b" * 40
    builder.build(scratch, check=True)
    source = scratch / "html-plan/skills/html-plan/SKILL.md"
    source.write_text(source.read_text().replace("Plan this: $ARGUMENTS", "A changed invocation contract"))
    before = builder.files(scratch / builder.PACKAGE)
    try:
        builder.build(scratch, "c" * 40)
    except ValueError as error:
        assert "review adapter" in str(error)
    else:
        raise AssertionError("Changed upstream contract must stop publication")
    assert builder.files(scratch / builder.PACKAGE) == before, "Last working package must survive failure"

with tempfile.TemporaryDirectory(dir=ROOT / "artifacts") as temp:
    scratch = Path(temp)
    shutil.copytree(package, scratch / builder.PACKAGE)
    shutil.copy(ROOT / "codex-upstream.lock.json", scratch)
    fake = scratch / "bin/gh"
    fake.parent.mkdir()
    fake.write_text('''#!/usr/bin/env python3
import json, os, pathlib, sys
with pathlib.Path("calls.log").open("a") as log:
    log.write(" ".join(sys.argv[1:]) + "\\n")
if sys.argv[2] == "view":
    v = json.loads(pathlib.Path("codex-upstream.lock.json").read_text())["version"]
    f = "html-plan-codex-" + v + ".zip"
    print(json.dumps({"isDraft": os.environ["RELEASE_STATE"] == "draft", "assets": [{"name": f}, {"name": f + ".sha256"}]}))
''')
    fake.chmod(0o755)
    for state in ["draft", "complete"]:
        log = scratch / "calls.log"
        log.unlink(missing_ok=True)
        subprocess.run(["bash", str(ROOT / "scripts/release.sh")], cwd=scratch, check=True,
                       env={**os.environ, "PATH": str(fake.parent) + os.pathsep + os.environ["PATH"], "RELEASE_STATE": state},
                       stdout=subprocess.DEVNULL)
        calls = log.read_text()
        assert "release create" not in calls, "Recovery must reuse the existing tag"
        assert ("release upload" in calls) == (state == "draft")
        assert ("release edit" in calls) == (state == "draft")

runtime = package / "skills/html-plan-codex/runtime"
for filename in ["tests/smoke.html", "plugins/html-plan-codex/skills/html-plan-codex/examples/scheduled-send.html"]:
    output = ROOT / "artifacts" / (Path(filename).stem + ".packed.html")
    subprocess.run(["node", str(runtime / "pack.mjs"), filename, "--root", str(ROOT), "-o", str(output)], cwd=ROOT, check=True)
    html = output.read_text()
    assert "data-htmlplan" in html and "<doc-plan>" in html
    assert "Copy this and paste it to Codex." in html
print("PASS: reproducibility, controlled runtime edits, version bump, drift stop, last-good preservation, draft recovery, release no-op, Chinese and upstream pack")

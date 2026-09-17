"""The text customers receive in the sdist and wheel stays accurate and public.

These files ship: the sdist carries the docs, examples and tests, the wheel
carries the `vedika` package, and the README becomes the PyPI description.
"""

import re
from pathlib import Path

PACKAGE_ROOT = Path(__file__).resolve().parent.parent
EXAMPLES = PACKAGE_ROOT / "examples"

# Internal tracker ids (task, audit and incident ids), pull-request numbers and
# deployment-status notes mean nothing to a customer and go stale.
INTERNAL_REFERENCE = re.compile(
    r"(?<![A-Za-z0-9_])(?:[MRP]-\d{3}|SDK-\d{1,3}|INC-\d{8}(?:-\d+)?)(?![0-9])"
    r"|\bPR #\d+|not\s+yet\s+deployed|docs[/]ops[/]",
    re.IGNORECASE,
)


def shipped_text_files():
    files = [PACKAGE_ROOT / name for name in ("README.md", "CHANGELOG.md", "SECURITY.md", "CONTRIBUTING.md", "setup.py")]
    for folder, pattern in (("vedika", "*.py"), ("examples", "*"), ("tests", "*.py")):
        files.extend(path for path in sorted((PACKAGE_ROOT / folder).rglob(pattern)) if path.is_file())
    return files


def listed_examples(markdown):
    return set(re.findall(r"^\s*- \*{0,2}`([\w.-]+\.py)`", markdown, re.MULTILINE))


def test_shipped_text_carries_no_internal_references():
    offenders = []
    for path in shipped_text_files():
        for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
            if INTERNAL_REFERENCE.search(line):
                offenders.append(f"{path.relative_to(PACKAGE_ROOT)}:{number}: {line.strip()[:120]}")
    assert offenders == []
    # Known-positive control: the pattern fires on the shapes that shipped before.
    for sample in ("origin (M-" + "027, 2026-09-09)", "(API change, PR #" + "844)", "routing (R-" + "004)"):
        assert INTERNAL_REFERENCE.search(sample)
    assert not INTERNAL_REFERENCE.search("SHA-256, UTF-8, ISO-8601 and Brihat Samhita 53.43-48")


def test_security_policy_names_only_real_key_classes():
    policy = (PACKAGE_ROOT / "SECURITY.md").read_text(encoding="utf-8")
    for prefix in ("vk_live_", "vk_ent_", "vk_sandbox_"):
        assert f"`{prefix}`" in policy
    for line in policy.splitlines():
        if "vk_test_" in line:
            assert "reject" in line, f"vk_test_ keys are rejected by the API, but SECURITY.md says: {line}"


def test_readme_example_lists_match_the_examples_directory():
    on_disk = {path.name for path in EXAMPLES.glob("*.py")}
    for document in (PACKAGE_ROOT / "README.md", EXAMPLES / "README.md"):
        listed = listed_examples(document.read_text(encoding="utf-8"))
        assert listed - on_disk == set(), f"{document.name} lists examples that do not exist"
        assert on_disk - listed == set(), f"{document.name} omits examples that exist"


def test_links_use_the_public_github_organisation():
    retired_org = "github.com/" + "vedika-intelligence"  # this organisation returns 404
    for path in shipped_text_files():
        assert retired_org not in path.read_text(encoding="utf-8"), path.name


# Rule 11: the public text names what the API does, never how it is built. Each
# of these shipped once and was removed: an agent count, a routing architecture,
# an internal build number, and pipeline stage names that are not even real SSE
# events.
ARCHITECTURE = re.compile(r"\b\d+\s*(?:AI\s*)?agents?\b|multi-?model|\bswarm\b|\bconsensus\b|\borchestrat", re.IGNORECASE)
INTERNAL_VERSION = re.compile(r"\(v\d{2}[:\s)]", re.IGNORECASE)
PIPELINE_STAGE = re.compile(r"'(?:synthesis|consensus|optimized_path|single_path)'", re.IGNORECASE)


def test_shipped_text_describes_no_internal_architecture():
    offenders = []
    for path in shipped_text_files():
        if path.name.startswith("test_"):
            continue  # this file names the patterns it forbids
        for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
            if ARCHITECTURE.search(line) or INTERNAL_VERSION.search(line) or PIPELINE_STAGE.search(line):
                offenders.append(f"{path.relative_to(PACKAGE_ROOT)}:{number}: {line.strip()[:120]}")
    assert offenders == []
    # Known-positive controls: the exact shapes that shipped before.
    assert ARCHITECTURE.search("[Detailed astrological insights from 6 AI agents]")
    assert ARCHITECTURE.search("**Advanced Multi-Model AI** (intelligent query routing)")
    assert INTERNAL_VERSION.search("**Voice AI** (v33: 3-tier voice interface)")
    assert PIPELINE_STAGE.search("# Events: 'started', 'synthesis', 'completed'")
    # And they leave ordinary product copy alone.
    assert not ARCHITECTURE.search("Multi-Turn Conversations (maintain context via conversation_id)")
    assert not INTERNAL_VERSION.search("Supported since v3 of the API")

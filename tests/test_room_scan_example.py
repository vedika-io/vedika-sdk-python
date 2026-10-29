"""examples/room_scan.py as a user runs it: a dry run by default, nothing is sent."""
import importlib.util
import json
import os
import subprocess
import sys
from pathlib import Path
from reference_fixtures import reference_path

ROOT = Path(__file__).resolve().parents[1]
EXAMPLE = ROOT / "examples" / "room_scan.py"


def run(*args, env=None):
    clean = {k: v for k, v in os.environ.items() if k != "VEDIKA_API_KEY"}
    clean["PYTHONPATH"] = str(ROOT)
    clean.update(env or {})
    done = subprocess.run([sys.executable, str(EXAMPLE), *args], env=clean, capture_output=True, text=True, timeout=60)
    return done.returncode, done.stdout


def requests(stdout):
    return [json.loads(line[8:]) for line in stdout.splitlines() if line.startswith("REQUEST ")]


def test_dry_run_uploads_twice_under_one_key_and_merges_under_its_own():
    code, out = run()
    assert code == 0, out
    sent = requests(out)
    assert [r["operation"] for r in sent] == ["ar/room-capture", "ar/room-capture", "ar/capture-merge"]
    assert sent[0]["idempotencyKey"] == "room-fx-room-3x4-yaw0"
    assert sent[1]["idempotencyKey"] == sent[0]["idempotencyKey"]
    assert sent[2]["idempotencyKey"] == "merge-fx-room-3x4-yaw0"


def test_untagged_capture_and_keyless_merge_are_refused_before_any_request():
    _, out = run()
    assert "REFUSED untagged capture:" in out and "Tag at least one room" in out
    assert "REFUSED merge without a key:" in out and "idempotency_key" in out
    assert len(requests(out)) == 3


def test_live_without_a_key_stops_without_sending():
    code, out = run("--live")
    assert code == 1
    assert "Set VEDIKA_API_KEY" in out
    assert requests(out) == []


# The dry run validates nothing, so the payloads are held to the fixtures the server's own tests use.
FIXTURE = reference_path("sdks/fixtures/vastu-room-capture/room-3x4-yaw0.json", "room-capture.json")


def load_example():
    spec = importlib.util.spec_from_file_location("room_scan_example", EXAMPLE)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_the_sample_capture_is_the_fixture_capture_the_server_accepts():
    assert load_example().CAPTURE == json.loads(FIXTURE.read_text())["expected"]["capture"]


def test_the_merge_body_has_two_captures_on_two_framed_floors_with_matching_room_floors():
    example = load_example()
    body = example.merge_body(example.CAPTURE)
    assert len(body["captures"]) == 2
    assert len({c["id"] for c in body["captures"]}) == 2
    assert len({c["payload"]["captureId"] for c in body["captures"]}) == 2
    frames = [f["floorIndex"] for f in body["floors"]]
    assert len(set(frames)) == len(frames)
    for c in body["captures"]:
        assert c["floorIndex"] in frames
        assert all(room["floorIndex"] == c["floorIndex"] for room in c["payload"]["rooms"])
        assert c["payload"]["quality"]["roomsTagged"] > 0

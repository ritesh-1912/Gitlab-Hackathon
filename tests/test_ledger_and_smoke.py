"""
Tests for build_ledger.py and smoke_test.py.
Verifies static HTML generation, provenance metrics, and in-process smoke tests.
"""

import json
import subprocess
import sys
from pathlib import Path

from scripts.build_ledger import build_ledger, generate_html
from scripts.smoke_test import run_in_process_smoke_test


def init_test_git_repo(repo_dir: Path) -> None:
    """Helper to initialize a git repo with a commit for ledger tests."""
    subprocess.run(["git", "init"], cwd=str(repo_dir), check=True, capture_output=True)
    subprocess.run(["git", "config", "user.name", "Ledger Tester"], cwd=str(repo_dir), check=True)
    subprocess.run(["git", "config", "user.email", "tester@ledger.local"], cwd=str(repo_dir), check=True)


def create_test_commit(repo_dir: Path, msg: str, filename: str = "file.txt") -> None:
    filepath = repo_dir / filename
    filepath.write_text("sample content\n")
    subprocess.run(["git", "add", filename], cwd=str(repo_dir), check=True, capture_output=True)
    subprocess.run(["git", "commit", "-m", msg], cwd=str(repo_dir), check=True, capture_output=True)


# ---------------------------------------------------------------------------
# Ledger Builder Tests
# ---------------------------------------------------------------------------

def test_build_ledger_creates_html(tmp_path: Path):
    init_test_git_repo(tmp_path)
    create_test_commit(tmp_path, "feat: initial commit\n\nAssisted-by: gitlab-duo", "a.txt")
    create_test_commit(tmp_path, "docs: add notes\n\nAssisted-by: none", "b.txt")

    out_dir = tmp_path / "public"
    index_file = build_ledger(
        output_dir=str(out_dir),
        gate_report_path=str(tmp_path / "nonexistent.json"),
        repo_dir=str(tmp_path),
        project_title="Test Accountability Ledger",
    )

    assert index_file.exists()
    content = index_file.read_text(encoding="utf-8")
    assert "Test Accountability Ledger" in content
    assert "Continuous Provenance Ledger" in content
    assert "Assisted-by: gitlab-duo" in content
    assert "Assisted-by: none" in content
    assert "Human Only" in content
    assert "AI-Assisted" in content


def test_build_ledger_with_gate_report(tmp_path: Path):
    init_test_git_repo(tmp_path)
    create_test_commit(tmp_path, "feat: add feature\n\nAssisted-by: none", "a.txt")

    gate_report_file = tmp_path / "gate_report.json"
    gate_data = {
        "gate_status": "PASSED",
        "summary": {
            "linked_issue": "#88",
            "total_violations": 0,
        },
        "violations": [],
    }
    gate_report_file.write_text(json.dumps(gate_data))

    out_dir = tmp_path / "public"
    index_file = build_ledger(
        output_dir=str(out_dir),
        gate_report_path=str(gate_report_file),
        repo_dir=str(tmp_path),
    )

    content = index_file.read_text(encoding="utf-8")
    assert "PASSED" in content
    assert "#88" in content
    assert "0 violation(s)" in content


def test_build_ledger_empty_repo(tmp_path: Path):
    init_test_git_repo(tmp_path)
    out_dir = tmp_path / "public"
    index_file = build_ledger(output_dir=str(out_dir), repo_dir=str(tmp_path))
    assert index_file.exists()
    content = index_file.read_text(encoding="utf-8")
    assert "0.0%" in content


def test_build_ledger_cli(tmp_path: Path):
    init_test_git_repo(tmp_path)
    create_test_commit(tmp_path, "feat: cli test\n\nAssisted-by: none", "c.txt")

    script_path = Path(__file__).resolve().parent.parent / "scripts" / "build_ledger.py"
    out_dir = tmp_path / "public"

    res = subprocess.run(
        [
            sys.executable,
            str(script_path),
            "--output-dir",
            str(out_dir),
            "--repo-dir",
            str(tmp_path),
        ],
        capture_output=True,
        text=True,
    )
    assert res.returncode == 0
    assert (out_dir / "index.html").exists()


# ---------------------------------------------------------------------------
# Smoke Test Runner Tests
# ---------------------------------------------------------------------------

def test_smoke_test_in_process_success():
    success, message = run_in_process_smoke_test(fail_on_purpose=False)
    assert success is True
    assert "All smoke tests passed" in message


def test_smoke_test_in_process_fail_on_purpose():
    success, message = run_in_process_smoke_test(fail_on_purpose=True)
    assert success is False
    assert "CRITICAL: Healthcheck failed" in message


def test_smoke_test_cli_success():
    script_path = Path(__file__).resolve().parent.parent / "scripts" / "smoke_test.py"
    res = subprocess.run([sys.executable, str(script_path)], capture_output=True, text=True)
    assert res.returncode == 0
    assert "RESULT: PASSED" in res.stdout


def test_smoke_test_cli_fail_on_purpose():
    script_path = Path(__file__).resolve().parent.parent / "scripts" / "smoke_test.py"
    res = subprocess.run(
        [sys.executable, str(script_path), "--fail-on-purpose"],
        capture_output=True,
        text=True,
    )
    assert res.returncode == 1
    assert "RESULT: FAILED" in res.stderr
    assert "CRITICAL: Healthcheck failed" in res.stderr

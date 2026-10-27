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
    """Helper to initialize a git repo with a commit for ledger tests with explicit branch and identity."""
    import os
    os.environ["GIT_AUTHOR_NAME"] = "Ledger Tester"
    os.environ["GIT_AUTHOR_EMAIL"] = "tester@ledger.local"
    os.environ["GIT_COMMITTER_NAME"] = "Ledger Tester"
    os.environ["GIT_COMMITTER_EMAIL"] = "tester@ledger.local"
    subprocess.run(["git", "init", "-b", "main"], cwd=str(repo_dir), check=True, capture_output=True)
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


def test_build_ledger_with_failed_gate_report_renders_violations(tmp_path: Path):
    init_test_git_repo(tmp_path)
    create_test_commit(tmp_path, "feat: bad commit", "bad.txt")

    gate_report_file = tmp_path / "gate_report.json"
    gate_data = {
        "gate_status": "FAILED",
        "summary": {
            "linked_issue": "#99",
            "total_violations": 2,
        },
        "violations": [
            "Commit abc1234 is missing a valid 'Assisted-by:' trailer",
            "Secret detected: Fake API Key in src/app.py:10",
        ],
    }
    gate_report_file.write_text(json.dumps(gate_data))

    out_dir = tmp_path / "public"
    index_file = build_ledger(
        output_dir=str(out_dir),
        gate_report_path=str(gate_report_file),
        repo_dir=str(tmp_path),
    )

    content = index_file.read_text(encoding="utf-8")
    assert "FAILED" in content
    assert "Reported Gate Violations (2)" in content
    assert "Commit abc1234 is missing a valid &#x27;Assisted-by:&#x27; trailer" in content or "Commit abc1234 is missing" in content
    assert "Secret detected: Fake API Key" in content


def test_build_ledger_malformed_gate_report_no_false_pass(tmp_path: Path):
    init_test_git_repo(tmp_path)
    create_test_commit(tmp_path, "feat: commit\n\nAssisted-by: none", "a.txt")

    gate_report_file = tmp_path / "gate_report.json"
    gate_report_file.write_text("{ broken json, not valid")

    out_dir = tmp_path / "public"
    index_file = build_ledger(
        output_dir=str(out_dir),
        gate_report_path=str(gate_report_file),
        repo_dir=str(tmp_path),
    )

    content = index_file.read_text(encoding="utf-8")
    assert "INVALID REPORT" in content
    assert "PASSED" not in content


def test_build_ledger_missing_gate_report_no_false_pass(tmp_path: Path):
    init_test_git_repo(tmp_path)
    create_test_commit(tmp_path, "feat: commit\n\nAssisted-by: none", "a.txt")

    missing_report = tmp_path / "missing_gate_report.json"
    out_dir = tmp_path / "public"
    index_file = build_ledger(
        output_dir=str(out_dir),
        gate_report_path=str(missing_report),
        repo_dir=str(tmp_path),
    )

    content = index_file.read_text(encoding="utf-8")
    assert "NOT AVAILABLE" in content
    # Should not show a false pass badge
    assert '<span class="badge badge-pass">PASSED</span>' not in content


def test_build_ledger_escapes_xss_content(tmp_path: Path):
    init_test_git_repo(tmp_path)
    create_test_commit(
        tmp_path,
        "<script>alert('xss')</script>\n\nAssisted-by: <img src=x onerror=alert(1)>",
        "xss.txt",
    )

    out_dir = tmp_path / "public"
    index_file = build_ledger(
        output_dir=str(out_dir),
        gate_report_path=str(tmp_path / "none.json"),
        repo_dir=str(tmp_path),
    )

    content = index_file.read_text(encoding="utf-8")
    assert "<script>alert('xss')</script>" not in content
    assert "&lt;script&gt;alert(&#x27;xss&#x27;)&lt;/script&gt;" in content or "&lt;script&gt;" in content
    assert "<img src=x" not in content
    assert "&lt;img src=x" in content


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


def test_build_ledger_excludes_merge_commits(tmp_path: Path):
    init_test_git_repo(tmp_path)
    create_test_commit(tmp_path, "feat: base commit\n\nAssisted-by: none", "base.txt")

    # Create a feature branch and commit
    subprocess.run(["git", "checkout", "-b", "feature"], cwd=str(tmp_path), check=True, capture_output=True)
    create_test_commit(tmp_path, "feat: branch commit\n\nAssisted-by: gitlab-duo", "feat.txt")

    # Back to main, create another commit to make a real merge
    subprocess.run(["git", "checkout", "main"], cwd=str(tmp_path), check=True, capture_output=True)
    create_test_commit(tmp_path, "feat: main commit\n\nAssisted-by: none", "main.txt")

    # Merge feature branch with --no-ff
    subprocess.run(["git", "merge", "--no-ff", "-m", "Merge branch feature", "feature"], cwd=str(tmp_path), check=True, capture_output=True)

    out_dir = tmp_path / "public"
    index_file = build_ledger(
        output_dir=str(out_dir),
        repo_dir=str(tmp_path),
    )
    content = index_file.read_text(encoding="utf-8")
    assert "Merge (excluded)" in content
    assert "Merge Commits" in content
    assert "1 excluded" in content
    # 3 evaluated commits, all 3 compliant -> 100.0% compliance
    assert "100.0%" in content
    assert "3 of 3 evaluated commits compliant" in content


def test_build_ledger_grandfathers_baseline_commits(tmp_path: Path):
    init_test_git_repo(tmp_path)
    # Starter commit lacks trailer
    create_test_commit(tmp_path, "Initial starter commit", "starter.txt")
    res = subprocess.run(["git", "rev-parse", "HEAD"], cwd=str(tmp_path), check=True, capture_output=True, text=True)
    starter_sha = res.stdout.strip()

    # Subsequent commit has trailer
    create_test_commit(tmp_path, "feat: compliant commit\n\nAssisted-by: gitlab-duo", "new.txt")

    out_dir = tmp_path / "public"
    index_file = build_ledger(
        output_dir=str(out_dir),
        repo_dir=str(tmp_path),
        baseline_sha=starter_sha,
    )
    content = index_file.read_text(encoding="utf-8")
    assert "Grandfathered (pre-contract)" in content
    assert "Grandfathered Commits" in content
    assert "1 grandfathered" in content
    # Evaluated is 1 commit, which is compliant -> 100.0%
    assert "100.0%" in content
    assert "1 of 1 evaluated commits compliant" in content
    assert "enforced provenance contract" in content
    assert "immutable provenance contract" not in content


def test_build_ledger_baseline_via_environment_variable(tmp_path: Path, monkeypatch):
    init_test_git_repo(tmp_path)
    create_test_commit(tmp_path, "Legacy unassisted root", "legacy.txt")
    res = subprocess.run(["git", "rev-parse", "HEAD"], cwd=str(tmp_path), check=True, capture_output=True, text=True)
    root_sha = res.stdout.strip()

    create_test_commit(tmp_path, "feat: assisted commit\n\nAssisted-by: Antigravity", "app.py")

    monkeypatch.setenv("ACCOUNTABILITY_BASELINE_SHA", root_sha)
    out_dir = tmp_path / "public"
    index_file = build_ledger(
        output_dir=str(out_dir),
        repo_dir=str(tmp_path),
    )
    content = index_file.read_text(encoding="utf-8")
    assert "Grandfathered (pre-contract)" in content
    assert "100.0%" in content


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

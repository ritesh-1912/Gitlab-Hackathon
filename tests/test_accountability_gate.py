"""
Unit and integration tests for the Accountability Gate.
Verifies commit provenance, intent issue linkage, secret detection parsing,
and CLI behavior using isolated temporary Git repositories.
"""

import json
import os
import subprocess
import sys
from pathlib import Path
import pytest

from scripts.accountability_gate import (
    parse_trailer_from_text,
    check_provenance,
    check_intent,
    check_secrets,
    run_gate,
)


def init_git_repo(repo_dir: Path) -> None:
    """Initializes a local git repository for testing with explicit branch and identity."""
    os.environ["GIT_AUTHOR_NAME"] = "Gate Test Runner"
    os.environ["GIT_AUTHOR_EMAIL"] = "gate@test.local"
    os.environ["GIT_COMMITTER_NAME"] = "Gate Test Runner"
    os.environ["GIT_COMMITTER_EMAIL"] = "gate@test.local"
    subprocess.run(["git", "init", "-b", "main"], cwd=str(repo_dir), check=True, capture_output=True)
    subprocess.run(["git", "config", "user.name", "Gate Test Runner"], cwd=str(repo_dir), check=True)
    subprocess.run(["git", "config", "user.email", "gate@test.local"], cwd=str(repo_dir), check=True)


def create_commit(repo_dir: Path, message: str, filename: str = "file.txt", content: str = "data\n") -> str:
    """Creates a commit with given message and returns its SHA."""
    filepath = repo_dir / filename
    filepath.write_text(content)
    subprocess.run(["git", "add", filename], cwd=str(repo_dir), check=True, capture_output=True)
    subprocess.run(["git", "commit", "-m", message], cwd=str(repo_dir), check=True, capture_output=True)
    res = subprocess.run(
        ["git", "rev-parse", "HEAD"], cwd=str(repo_dir), check=True, capture_output=True, text=True
    )
    return res.stdout.strip()


# ---------------------------------------------------------------------------
# Unit Tests: Trailer Parser
# ---------------------------------------------------------------------------

def test_trailer_parser_valid_named_tool():
    msg = "feat: add user login\n\nImplements JWT authentication.\n\nAssisted-by: gitlab-duo"
    assert parse_trailer_from_text(msg) == "gitlab-duo"


def test_trailer_parser_valid_assisted_by_none():
    msg = "fix: handle null pointer\n\nAssisted-by: none"
    assert parse_trailer_from_text(msg) == "none"


def test_trailer_parser_multiple_trailers():
    msg = (
        "refactor: extract helper\n\n"
        "Assisted-by: copilot\n"
        "Signed-off-by: Developer <dev@example.com>"
    )
    assert parse_trailer_from_text(msg) == "copilot"


def test_trailer_parser_rejects_sentence_mention():
    msg = (
        "feat: add export feature\n\n"
        "I was Assisted-by: none when writing this sentence in the body.\n"
        "Not a real trailer."
    )
    assert parse_trailer_from_text(msg) is None


def test_trailer_parser_rejects_empty_value():
    msg = "docs: update readme\n\nAssisted-by:"
    assert parse_trailer_from_text(msg) is None


def test_trailer_parser_no_trailers():
    msg = "chore: bump version\n\nJust a simple version bump without trailers."
    assert parse_trailer_from_text(msg) is None


# ---------------------------------------------------------------------------
# Tests: Provenance Check in Temporary Git Repos
# ---------------------------------------------------------------------------

def test_provenance_valid_assisted_by_none(tmp_path: Path):
    init_git_repo(tmp_path)
    base_sha = create_commit(tmp_path, "Initial commit\n\nAssisted-by: none", "init.txt", "v1\n")
    head_sha = create_commit(tmp_path, "Feature A\n\nAssisted-by: none", "feat.txt", "v2\n")

    res, violations = check_provenance(base=base_sha, head=head_sha, repo_dir=str(tmp_path))
    assert res["status"] == "PASSED"
    assert res["valid_trailers_count"] == 1
    assert len(violations) == 0
    assert res["commits"][0]["assisted_by"] == "none"
    assert res["commits"][0]["valid_trailer"] is True


def test_provenance_valid_named_agent(tmp_path: Path):
    init_git_repo(tmp_path)
    base_sha = create_commit(tmp_path, "Initial commit\n\nAssisted-by: none", "init.txt", "v1\n")
    head_sha = create_commit(tmp_path, "AI Feature\n\nAssisted-by: gitlab-duo", "ai.txt", "v2\n")

    res, violations = check_provenance(base=base_sha, head=head_sha, repo_dir=str(tmp_path))
    assert res["status"] == "PASSED"
    assert res["valid_trailers_count"] == 1
    assert len(violations) == 0
    assert res["commits"][0]["assisted_by"] == "gitlab-duo"
    assert res["commits"][0]["valid_trailer"] is True


def test_provenance_missing_trailer(tmp_path: Path):
    init_git_repo(tmp_path)
    base_sha = create_commit(tmp_path, "Base commit\n\nAssisted-by: none", "init.txt", "v1\n")
    head_sha = create_commit(tmp_path, "Missing trailer\n\nSome body without trailer.", "bad.txt", "v2\n")

    res, violations = check_provenance(base=base_sha, head=head_sha, repo_dir=str(tmp_path))
    assert res["status"] == "FAILED"
    assert res["valid_trailers_count"] == 0
    assert len(violations) == 1
    assert "missing a valid 'Assisted-by:' trailer" in violations[0]


def test_provenance_invalid_trailer_in_sentence(tmp_path: Path):
    init_git_repo(tmp_path)
    base_sha = create_commit(tmp_path, "Base commit\n\nAssisted-by: none", "init.txt", "v1\n")
    head_sha = create_commit(
        tmp_path,
        "Commit with inline mention\n\nThis mentions Assisted-by: none in a regular sentence.",
        "sentence.txt",
        "v2\n",
    )

    res, violations = check_provenance(base=base_sha, head=head_sha, repo_dir=str(tmp_path))
    assert res["status"] == "FAILED"
    assert len(violations) == 1
    assert "missing a valid 'Assisted-by:' trailer" in violations[0]


def test_provenance_empty_range(tmp_path: Path):
    init_git_repo(tmp_path)
    sha = create_commit(tmp_path, "Single commit\n\nAssisted-by: none", "file.txt", "v1\n")

    # Range sha..sha has 0 commits
    res, violations = check_provenance(base=sha, head=sha, repo_dir=str(tmp_path))
    assert res["status"] == "FAILED"
    assert any("contains no commits to inspect" in v for v in violations)


def test_provenance_unavailable_commit_range(tmp_path: Path):
    init_git_repo(tmp_path)
    head_sha = create_commit(tmp_path, "Single commit\n\nAssisted-by: none", "file.txt", "v1\n")

    res, violations = check_provenance(base="deadbeef00000000000000000000000000000000", head=head_sha, repo_dir=str(tmp_path))
    assert res["status"] == "FAILED"
    assert any("Git command failed" in v for v in violations)


def test_provenance_missing_base(tmp_path: Path):
    res, violations = check_provenance(base=None, head="HEAD", repo_dir=str(tmp_path))
    assert res["status"] == "FAILED"
    assert any("Cannot determine base commit" in v for v in violations)


# ---------------------------------------------------------------------------
# Tests: Intent Check
# ---------------------------------------------------------------------------

def test_intent_valid_closes_reference():
    desc = "This merge request adds item filtering.\n\nCloses #42"
    res, violations = check_intent(desc)
    assert res["status"] == "PASSED"
    assert res["linked_issue"] == "#42"
    assert res["issue_iid"] == 42
    assert res["keyword"] == "Closes"
    assert len(violations) == 0


def test_intent_valid_fixes_reference():
    desc = "Resolves issue.\nFixes #108\nThank you."
    res, violations = check_intent(desc)
    assert res["status"] == "PASSED"
    assert res["linked_issue"] == "#108"
    assert res["issue_iid"] == 108
    assert res["keyword"] == "Fixes"
    assert len(violations) == 0


def test_intent_case_insensitive():
    desc = "closes #5"
    res, violations = check_intent(desc)
    assert res["status"] == "PASSED"
    assert res["linked_issue"] == "#5"


def test_intent_missing_description():
    res, violations = check_intent(None)
    assert res["status"] == "FAILED"
    assert any("failed closed" in v for v in violations)


def test_intent_empty_description():
    res, violations = check_intent("   ")
    assert res["status"] == "FAILED"
    assert any("description is empty" in v for v in violations)


def test_intent_unrecognized_keyword():
    desc = "This PR relates to #42 and connects with #99."
    res, violations = check_intent(desc)
    assert res["status"] == "FAILED"
    assert any("Missing valid issue reference" in v for v in violations)


# ---------------------------------------------------------------------------
# Tests: Secret Detection
# ---------------------------------------------------------------------------

def test_secret_detection_absent(tmp_path: Path):
    missing_path = tmp_path / "gl-secret-detection-report.json"
    res, violations = check_secrets(str(missing_path), require_report=False)
    assert res["status"] == "NOT_SUPPLIED"
    assert res["findings_count"] == 0
    assert len(violations) == 0


def test_secret_detection_clean_report(tmp_path: Path):
    report_file = tmp_path / "gl-secret-detection-report.json"
    report_data = {
        "version": "15.0.0",
        "vulnerabilities": [],
    }
    report_file.write_text(json.dumps(report_data))

    res, violations = check_secrets(str(report_file))
    assert res["status"] == "PASSED"
    assert res["findings_count"] == 0
    assert len(violations) == 0


def test_secret_detection_with_findings(tmp_path: Path):
    report_file = tmp_path / "gl-secret-detection-report.json"
    report_data = {
        "version": "15.0.0",
        "vulnerabilities": [
            {
                "id": "sec-1",
                "name": "AWS API Key",
                "severity": "Critical",
                "location": {
                    "file": "src/app.py",
                    "start_line": 12,
                },
            }
        ],
    }
    report_file.write_text(json.dumps(report_data))

    res, violations = check_secrets(str(report_file))
    assert res["status"] == "FAILED"
    assert res["findings_count"] == 1
    assert len(violations) == 1
    assert "Secret detected: AWS API Key" in violations[0]


def test_secret_detection_malformed_json(tmp_path: Path):
    report_file = tmp_path / "gl-secret-detection-report.json"
    report_file.write_text("{ broken json: true, ")

    res, violations = check_secrets(str(report_file))
    assert res["status"] == "ERROR"
    assert any("Malformed Secret Detection report" in v for v in violations)


def test_secret_detection_invalid_schema(tmp_path: Path):
    report_file = tmp_path / "gl-secret-detection-report.json"
    report_file.write_text(json.dumps({"wrong_key": 123}))

    res, violations = check_secrets(str(report_file))
    assert res["status"] == "ERROR"
    assert any("missing 'vulnerabilities' key" in v for v in violations)


# ---------------------------------------------------------------------------
# Integration Tests: run_gate and CLI Execution
# ---------------------------------------------------------------------------

def test_run_gate_full_pass(tmp_path: Path):
    init_git_repo(tmp_path)
    base_sha = create_commit(tmp_path, "Base commit\n\nAssisted-by: none", "init.txt", "base\n")
    head_sha = create_commit(tmp_path, "Add item endpoint\n\nAssisted-by: gitlab-duo", "feat.txt", "item\n")

    report_path = tmp_path / "gate_report.json"
    exit_code, report = run_gate(
        base=base_sha,
        head=head_sha,
        description="Implements inventory item creation.\n\nCloses #7",
        secret_report=str(tmp_path / "gl-secret-detection-report.json"),
        output_path=str(report_path),
        repo_dir=str(tmp_path),
    )

    assert exit_code == 0
    assert report["gate_status"] == "PASSED"
    assert report["summary"]["linked_issue"] == "#7"
    assert report["summary"]["valid_trailers"] == 1
    assert len(report["violations"]) == 0
    assert report_path.exists()


def test_cli_execution_success(tmp_path: Path):
    init_git_repo(tmp_path)
    base_sha = create_commit(tmp_path, "Base commit\n\nAssisted-by: none", "init.txt", "base\n")
    head_sha = create_commit(tmp_path, "Feature commit\n\nAssisted-by: none", "feat.txt", "data\n")

    report_path = tmp_path / "gate_report.json"
    script_path = Path(__file__).resolve().parent.parent / "scripts" / "accountability_gate.py"

    cmd = [
        sys.executable,
        str(script_path),
        "--base",
        base_sha,
        "--head",
        head_sha,
        "--description",
        "Adds feature. Closes #12",
        "--output",
        str(report_path),
        "--repo-dir",
        str(tmp_path),
    ]

    res = subprocess.run(cmd, capture_output=True, text=True)
    assert res.returncode == 0
    assert "ACCOUNTABILITY GATE: PASSED" in res.stdout
    assert report_path.exists()

    with open(report_path) as f:
        data = json.load(f)
    assert data["gate_status"] == "PASSED"
    assert data["summary"]["linked_issue"] == "#12"


def test_cli_execution_failure_missing_trailer(tmp_path: Path):
    init_git_repo(tmp_path)
    base_sha = create_commit(tmp_path, "Base commit\n\nAssisted-by: none", "init.txt", "base\n")
    head_sha = create_commit(tmp_path, "Feature commit without trailer", "feat.txt", "data\n")

    report_path = tmp_path / "gate_report.json"
    script_path = Path(__file__).resolve().parent.parent / "scripts" / "accountability_gate.py"

    cmd = [
        sys.executable,
        str(script_path),
        "--base",
        base_sha,
        "--head",
        head_sha,
        "--description",
        "Adds feature. Closes #12",
        "--output",
        str(report_path),
        "--repo-dir",
        str(tmp_path),
    ]

    res = subprocess.run(cmd, capture_output=True, text=True)
    assert res.returncode == 1
    assert "ACCOUNTABILITY GATE: FAILED" in res.stdout
    assert report_path.exists()

    with open(report_path) as f:
        data = json.load(f)
    assert data["gate_status"] == "FAILED"
    assert len(data["violations"]) >= 1


def test_provenance_excludes_merge_commits(tmp_path: Path):
    init_git_repo(tmp_path)
    base_sha = create_commit(tmp_path, "Base commit\n\nAssisted-by: none", "init.txt", "base\n")

    # Feature branch commit
    subprocess.run(["git", "checkout", "-b", "feature"], cwd=str(tmp_path), check=True, capture_output=True)
    create_commit(tmp_path, "Feature commit\n\nAssisted-by: gitlab-duo", "feat.txt", "feat\n")

    # Switch back to main and add another commit
    subprocess.run(["git", "checkout", "main"], cwd=str(tmp_path), check=True, capture_output=True)
    create_commit(tmp_path, "Main commit\n\nAssisted-by: none", "main.txt", "main\n")

    # Merge feature branch creating a merge commit without trailer
    subprocess.run(
        ["git", "merge", "--no-ff", "feature", "-m", "Merge branch feature into main"],
        cwd=str(tmp_path),
        check=True,
        capture_output=True,
    )

    res, violations = check_provenance(base=base_sha, head="HEAD", repo_dir=str(tmp_path), no_merges=True)
    assert res["status"] == "PASSED"
    assert res["skipped_merges_count"] == 1
    assert res["total_commits"] == 2  # Feature commit + main commit (merge commit excluded)
    assert res["valid_trailers_count"] == 2
    assert len(violations) == 0


def test_push_mode_normal_range(tmp_path: Path):
    init_git_repo(tmp_path)
    base_sha = create_commit(tmp_path, "Base commit\n\nAssisted-by: none", "init.txt", "base\n")
    head_sha = create_commit(tmp_path, "Direct push commit\n\nAssisted-by: gitlab-duo", "feat.txt", "feat\n")

    report_path = tmp_path / "gate_report.json"
    exit_code, report = run_gate(
        base=base_sha,
        head=head_sha,
        description=None,  # No MR description in push mode
        mode="push",
        secret_report=str(tmp_path / "gl-secret-detection-report.json"),
        output_path=str(report_path),
        repo_dir=str(tmp_path),
    )

    assert exit_code == 0
    assert report["gate_status"] == "PASSED"
    assert report["intent_check"]["status"] == "NOT_APPLICABLE"
    assert report["summary"]["mode"] == "push"
    assert len(report["violations"]) == 0


def test_push_mode_all_zeros_base_checks_only_head(tmp_path: Path):
    init_git_repo(tmp_path)
    create_commit(tmp_path, "Older commit\n\nAssisted-by: none", "init.txt", "base\n")
    head_sha = create_commit(tmp_path, "Head commit\n\nAssisted-by: gitlab-duo", "feat.txt", "feat\n")

    report_path = tmp_path / "gate_report.json"
    exit_code, report = run_gate(
        base="0000000000000000000000000000000000000000",
        head=head_sha,
        description=None,
        mode="push",
        secret_report=str(tmp_path / "gl-secret-detection-report.json"),
        output_path=str(report_path),
        repo_dir=str(tmp_path),
    )

    assert exit_code == 0
    assert report["gate_status"] == "PASSED"
    assert report["provenance_check"]["check_only_head"] is True
    assert report["provenance_check"]["total_commits"] == 1
    assert report["intent_check"]["status"] == "NOT_APPLICABLE"


def test_push_mode_all_zeros_base_fails_if_head_missing_trailer(tmp_path: Path):
    init_git_repo(tmp_path)
    create_commit(tmp_path, "Older commit\n\nAssisted-by: none", "init.txt", "base\n")
    head_sha = create_commit(tmp_path, "Head commit without trailer", "feat.txt", "feat\n")

    report_path = tmp_path / "gate_report.json"
    exit_code, report = run_gate(
        base="0000000000000000000000000000000000000000",
        head=head_sha,
        description=None,
        mode="push",
        secret_report=str(tmp_path / "gl-secret-detection-report.json"),
        output_path=str(report_path),
        repo_dir=str(tmp_path),
    )

    assert exit_code == 1
    assert report["gate_status"] == "FAILED"
    assert any("missing a valid 'Assisted-by:' trailer" in v for v in report["violations"])


def test_cli_execution_push_mode(tmp_path: Path):
    init_git_repo(tmp_path)
    head_sha = create_commit(tmp_path, "Push commit\n\nAssisted-by: none", "file.txt", "content\n")

    report_path = tmp_path / "gate_report.json"
    script_path = Path(__file__).resolve().parent.parent / "scripts" / "accountability_gate.py"

    cmd = [
        sys.executable,
        str(script_path),
        "--mode",
        "push",
        "--base",
        "0000000000000000000000000000000000000000",
        "--head",
        head_sha,
        "--output",
        str(report_path),
        "--repo-dir",
        str(tmp_path),
    ]

    res = subprocess.run(cmd, capture_output=True, text=True)
    assert res.returncode == 0
    assert "ACCOUNTABILITY GATE: PASSED" in res.stdout
    assert "Mode: PUSH" in res.stdout
    assert "Intent Check: NOT_APPLICABLE" in res.stdout


def test_baseline_sha_grandfathers_starter_commit(tmp_path: Path):
    init_git_repo(tmp_path)
    root_sha = create_commit(tmp_path, "Root commit\n\nAssisted-by: none", "root.txt", "root\n")
    starter_sha = create_commit(tmp_path, "Initial commit without trailer", "init.txt", "init\n")
    feature_sha = create_commit(
        tmp_path, "feat: user feature\n\nAssisted-by: gitlab-duo", "feat.txt", "feat\n"
    )

    report_path = tmp_path / "gate_report.json"
    exit_code, report = run_gate(
        base=root_sha,
        head=feature_sha,
        mode="push",
        baseline_sha=starter_sha,
        secret_report=str(tmp_path / "gl-secret-detection-report.json"),
        output_path=str(report_path),
        repo_dir=str(tmp_path),
    )

    assert exit_code == 0
    assert report["gate_status"] == "PASSED"
    summary = report["summary"]
    assert summary["grandfathered_commits"] == 1
    # Check that starter commit is listed as grandfathered
    starter_entry = next(c for c in report["provenance_check"]["commits"] if c["sha"] == starter_sha)
    assert starter_entry["grandfathered"] is True
    assert starter_entry["status"] == "GRANDFATHERED"


def test_baseline_sha_fails_unassisted_commit_after_baseline(tmp_path: Path):
    init_git_repo(tmp_path)
    starter_sha = create_commit(tmp_path, "Initial commit", "init.txt", "init\n")
    unassisted_sha = create_commit(tmp_path, "feat: rogue commit without trailer", "rogue.txt", "code\n")

    report_path = tmp_path / "gate_report.json"
    exit_code, report = run_gate(
        base="0000000000000000000000000000000000000000",
        head=unassisted_sha,
        mode="push",
        baseline_sha=starter_sha,
        secret_report=str(tmp_path / "gl-secret-detection-report.json"),
        output_path=str(report_path),
        repo_dir=str(tmp_path),
    )

    assert exit_code == 1
    assert report["gate_status"] == "FAILED"
    # Unassisted commit after baseline must cause violation
    assert any(unassisted_sha[:8] in v for v in report["violations"])
    # Starter commit must not cause violation
    assert not any(starter_sha[:8] in v for v in report["violations"])


def test_baseline_sha_via_environment_variable(tmp_path: Path, monkeypatch):
    init_git_repo(tmp_path)
    starter_sha = create_commit(tmp_path, "Legacy starter commit", "legacy.txt", "legacy\n")

    monkeypatch.setenv("ACCOUNTABILITY_BASELINE_SHA", starter_sha[:7])

    report_path = tmp_path / "gate_report.json"
    exit_code, report = run_gate(
        base="0000000000000000000000000000000000000000",
        head=starter_sha,
        mode="push",
        secret_report=str(tmp_path / "gl-secret-detection-report.json"),
        output_path=str(report_path),
        repo_dir=str(tmp_path),
    )

    assert exit_code == 0
    assert report["gate_status"] == "PASSED"
    assert report["summary"]["grandfathered_commits"] == 1

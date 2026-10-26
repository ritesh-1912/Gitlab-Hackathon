#!/usr/bin/env python3
"""
Accountability Gate for DevSecOps pipelines.

Validates:
1. Commit Provenance: Every commit in the MR contains a valid 'Assisted-by:' Git trailer.
2. Intent Linkage: MR description explicitly references an issue ('Closes #<id>' or 'Fixes #<id>').
3. Secret Detection: Parses gl-secret-detection-report.json if present; fails on any findings.

Generates a structured gate_report.json artifact and exits 0 on pass, non-zero on failure.
Does not require external GitLab API tokens or external network services.
"""

import argparse
import json
import os
import re
import subprocess
import sys
from typing import Any, Dict, List, Optional, Tuple


def parse_trailer_from_text(msg: str, key: str = "Assisted-by") -> Optional[str]:
    """
    Extracts a Git trailer value following Git's trailer conventions.
    A trailer must reside in the final paragraph of the commit message,
    where every line in that paragraph matches the 'Token: Value' trailer format.
    Arbitrary sentences in the body mentioning the token are rejected.
    """
    paragraphs = [p.strip() for p in re.split(r"\n\s*\n", msg.strip()) if p.strip()]
    if not paragraphs:
        return None

    last_paragraph = paragraphs[-1]
    lines = last_paragraph.splitlines()
    trailer_regex = re.compile(r"^([A-Za-z0-9_-]+):\s*(.*)$")

    trailers: Dict[str, str] = {}
    for line in lines:
        match = trailer_regex.match(line)
        if not match:
            # If any line in the final block does not match Key: Value, it is regular body text.
            return None
        token = match.group(1).lower()
        value = match.group(2).strip()
        trailers[token] = value

    val = trailers.get(key.lower())
    return val if (val is not None and len(val) > 0) else None


def get_commit_trailer_git(sha: str, key: str = "Assisted-by", repo_dir: str = ".") -> Optional[str]:
    """Uses git's built-in trailer parser as primary, falling back to Python trailer parser."""
    try:
        res = subprocess.run(
            ["git", "log", "-1", f"--format=%(trailers:key={key},valueonly=true)", sha],
            cwd=repo_dir,
            capture_output=True,
            text=True,
            check=False,
        )
        if res.returncode == 0 and res.stdout.strip():
            return res.stdout.strip()
    except Exception:
        pass

    # Fallback to inspecting raw commit message text
    try:
        res = subprocess.run(
            ["git", "log", "-1", "--format=%B", sha],
            cwd=repo_dir,
            capture_output=True,
            text=True,
            check=False,
        )
        if res.returncode == 0 and res.stdout.strip():
            return parse_trailer_from_text(res.stdout, key)
    except Exception:
        pass

    return None


def get_commit_subject(sha: str, repo_dir: str = ".") -> str:
    """Returns the one-line commit subject."""
    try:
        res = subprocess.run(
            ["git", "log", "-1", "--format=%s", sha],
            cwd=repo_dir,
            capture_output=True,
            text=True,
            check=False,
        )
        if res.returncode == 0:
            return res.stdout.strip()
    except Exception:
        pass
    return "Unknown subject"


def get_commits_in_range(base: str, head: str, repo_dir: str = ".") -> Tuple[List[str], Optional[str]]:
    """
    Returns list of commit SHAs between base and head (base..head).
    Returns (shas, error_message).
    """
    cmd = ["git", "rev-list", f"{base}..{head}"]
    try:
        res = subprocess.run(cmd, cwd=repo_dir, capture_output=True, text=True, check=False)
        if res.returncode != 0:
            err = res.stderr.strip() or f"git rev-list exited with code {res.returncode}"
            return [], f"Git command failed ('{' '.join(cmd)}'): {err}"

        shas = [line.strip() for line in res.stdout.splitlines() if line.strip()]
        return shas, None
    except Exception as e:
        return [], f"Exception executing git rev-list: {e}"


def check_provenance(
    base: Optional[str], head: str, repo_dir: str = "."
) -> Tuple[Dict[str, Any], List[str]]:
    """Validates that all commits in range base..head carry a valid Assisted-by trailer."""
    violations: List[str] = []

    if not base:
        violations.append(
            "Cannot determine base commit for merge request. "
            "In CI, ensure CI_MERGE_REQUEST_DIFF_BASE_SHA is set, or provide --base locally."
        )
        return {
            "status": "FAILED",
            "base_sha": None,
            "head_sha": head,
            "commits": [],
            "total_commits": 0,
            "valid_trailers_count": 0,
        }, violations

    shas, err = get_commits_in_range(base, head, repo_dir)
    if err:
        violations.append(err)
        return {
            "status": "FAILED",
            "base_sha": base,
            "head_sha": head,
            "commits": [],
            "total_commits": 0,
            "valid_trailers_count": 0,
        }, violations

    if not shas:
        violations.append(f"Commit range '{base}..{head}' contains no commits to inspect.")
        return {
            "status": "FAILED",
            "base_sha": base,
            "head_sha": head,
            "commits": [],
            "total_commits": 0,
            "valid_trailers_count": 0,
        }, violations

    inspected_commits = []
    valid_count = 0

    for sha in shas:
        subject = get_commit_subject(sha, repo_dir)
        trailer_val = get_commit_trailer_git(sha, "Assisted-by", repo_dir)

        is_valid = bool(trailer_val and trailer_val.strip())
        if is_valid:
            valid_count += 1
        else:
            violations.append(
                f"Commit {sha[:8]} ('{subject}') is missing a valid 'Assisted-by:' trailer "
                "(expected e.g. 'Assisted-by: gitlab-duo' or 'Assisted-by: none')."
            )

        inspected_commits.append({
            "sha": sha,
            "short_sha": sha[:8],
            "subject": subject,
            "assisted_by": trailer_val,
            "valid_trailer": is_valid,
        })

    status = "PASSED" if valid_count == len(shas) else "FAILED"
    return {
        "status": status,
        "base_sha": base,
        "head_sha": head,
        "commits": inspected_commits,
        "total_commits": len(shas),
        "valid_trailers_count": valid_count,
    }, violations


def check_intent(description: Optional[str]) -> Tuple[Dict[str, Any], List[str]]:
    """Validates that MR description references an issue via Closes #<id> or Fixes #<id>."""
    violations: List[str] = []

    if description is None:
        violations.append(
            "MR description check failed closed: Merge request description not provided "
            "or unavailable in environment (CI_MERGE_REQUEST_DESCRIPTION not set)."
        )
        return {"status": "FAILED", "linked_issue": None, "keyword": None}, violations

    if not description.strip():
        violations.append("MR description check failed: Merge request description is empty.")
        return {"status": "FAILED", "linked_issue": None, "keyword": None}, violations

    # Pattern: Closes #<number> or Fixes #<number>
    pattern = re.compile(r"\b(Closes|Fixes)\s+#(\d+)\b", re.IGNORECASE)
    match = pattern.search(description)

    if not match:
        violations.append(
            "MR description check failed: Missing valid issue reference. "
            "Expected 'Closes #<number>' or 'Fixes #<number>' in MR description."
        )
        return {"status": "FAILED", "linked_issue": None, "keyword": None}, violations

    keyword = match.group(1).capitalize()
    issue_num = match.group(2)

    return {
        "status": "PASSED",
        "linked_issue": f"#{issue_num}",
        "issue_iid": int(issue_num),
        "keyword": keyword,
    }, violations


def check_secrets(
    report_path: str, require_report: bool = False
) -> Tuple[Dict[str, Any], List[str]]:
    """
    Parses GitLab Secret Detection JSON report (gl-secret-detection-report.json).
    Fails if findings exist or report is malformed.
    Reports NOT_SUPPLIED if absent and require_report is False.
    """
    violations: List[str] = []

    if not os.path.exists(report_path):
        if require_report:
            violations.append(f"Secret Detection report required but not found at: {report_path}")
            return {
                "status": "FAILED",
                "report_path": report_path,
                "findings_count": 0,
                "findings": [],
            }, violations

        return {
            "status": "NOT_SUPPLIED",
            "report_path": report_path,
            "findings_count": 0,
            "findings": [],
        }, violations

    try:
        with open(report_path, "r", encoding="utf-8") as f:
            content = f.read()
        data = json.loads(content)
    except Exception as e:
        violations.append(f"Malformed Secret Detection report at {report_path}: {e}")
        return {
            "status": "ERROR",
            "report_path": report_path,
            "findings_count": 0,
            "findings": [],
        }, violations

    if not isinstance(data, dict) or "vulnerabilities" not in data:
        violations.append(
            f"Invalid Secret Detection report structure at {report_path}: missing 'vulnerabilities' key."
        )
        return {
            "status": "ERROR",
            "report_path": report_path,
            "findings_count": 0,
            "findings": [],
        }, violations

    vulns = data.get("vulnerabilities")
    if not isinstance(vulns, list):
        violations.append(
            f"Invalid Secret Detection report structure at {report_path}: 'vulnerabilities' is not a list."
        )
        return {
            "status": "ERROR",
            "report_path": report_path,
            "findings_count": 0,
            "findings": [],
        }, violations

    findings = []
    for v in vulns:
        if isinstance(v, dict):
            loc = v.get("location", {})
            finding_info = {
                "id": v.get("id", "unknown"),
                "name": v.get("name", "Secret Finding"),
                "severity": v.get("severity", "Unknown"),
                "file": loc.get("file", "unknown") if isinstance(loc, dict) else "unknown",
                "line": loc.get("start_line", 0) if isinstance(loc, dict) else 0,
            }
            findings.append(finding_info)
            violations.append(
                f"Secret detected: {finding_info['name']} (Severity: {finding_info['severity']}) "
                f"at {finding_info['file']}:{finding_info['line']}"
            )
        else:
            findings.append({"id": "unknown", "name": str(v), "severity": "Unknown", "file": "unknown", "line": 0})
            violations.append(f"Secret detected: {v}")

    status = "FAILED" if findings else "PASSED"
    return {
        "status": status,
        "report_path": report_path,
        "findings_count": len(findings),
        "findings": findings,
    }, violations


def resolve_base_ref(cli_base: Optional[str]) -> Tuple[Optional[str], str]:
    """Resolves base ref from CLI or CI environment variables."""
    if cli_base:
        return cli_base, "cli_argument"

    # GitLab MR pipeline variables
    diff_base = os.environ.get("CI_MERGE_REQUEST_DIFF_BASE_SHA")
    if diff_base:
        return diff_base, "CI_MERGE_REQUEST_DIFF_BASE_SHA"

    target_sha = os.environ.get("CI_MERGE_REQUEST_TARGET_BRANCH_SHA")
    if target_sha:
        return target_sha, "CI_MERGE_REQUEST_TARGET_BRANCH_SHA"

    target_branch = os.environ.get("CI_MERGE_REQUEST_TARGET_BRANCH_NAME")
    if target_branch:
        return f"origin/{target_branch}", "CI_MERGE_REQUEST_TARGET_BRANCH_NAME"

    return None, "unavailable"


def resolve_head_ref(cli_head: Optional[str]) -> Tuple[str, str]:
    """Resolves head ref from CLI or CI environment variables."""
    if cli_head:
        return cli_head, "cli_argument"

    ci_sha = os.environ.get("CI_COMMIT_SHA")
    if ci_sha:
        return ci_sha, "CI_COMMIT_SHA"

    return "HEAD", "default_HEAD"


def resolve_description(cli_desc: Optional[str]) -> Tuple[Optional[str], str]:
    """Resolves MR description from CLI or CI environment variables."""
    if cli_desc is not None:
        return cli_desc, "cli_argument"

    if "CI_MERGE_REQUEST_DESCRIPTION" in os.environ:
        return os.environ.get("CI_MERGE_REQUEST_DESCRIPTION"), "CI_MERGE_REQUEST_DESCRIPTION"

    return None, "unavailable"


def run_gate(
    base: Optional[str] = None,
    head: Optional[str] = None,
    description: Optional[str] = None,
    secret_report: str = "gl-secret-detection-report.json",
    require_secret_report: bool = False,
    output_path: str = "gate_report.json",
    repo_dir: str = ".",
) -> Tuple[int, Dict[str, Any]]:
    """Runs all gate checks and writes output report."""
    resolved_base, base_source = resolve_base_ref(base)
    resolved_head, head_source = resolve_head_ref(head)
    resolved_desc, desc_source = resolve_description(description)

    all_violations: List[str] = []

    # 1. Provenance Check
    prov_res, prov_violations = check_provenance(resolved_base, resolved_head, repo_dir)
    all_violations.extend(prov_violations)

    # 2. Intent Check
    intent_res, intent_violations = check_intent(resolved_desc)
    all_violations.extend(intent_violations)

    # 3. Secret Detection Check
    secret_res, secret_violations = check_secrets(secret_report, require_secret_report)
    all_violations.extend(secret_violations)

    gate_status = "PASSED" if not all_violations else "FAILED"
    exit_code = 0 if gate_status == "PASSED" else 1

    report_data = {
        "gate_status": gate_status,
        "summary": {
            "commits_inspected": prov_res.get("total_commits", 0),
            "valid_trailers": prov_res.get("valid_trailers_count", 0),
            "linked_issue": intent_res.get("linked_issue"),
            "secret_detection_status": secret_res.get("status"),
            "secret_findings_count": secret_res.get("findings_count", 0),
            "total_violations": len(all_violations),
        },
        "metadata": {
            "base_ref": resolved_base,
            "base_source": base_source,
            "head_ref": resolved_head,
            "head_source": head_source,
            "description_source": desc_source,
        },
        "provenance_check": prov_res,
        "intent_check": intent_res,
        "secret_detection_check": secret_res,
        "violations": all_violations,
    }

    try:
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(report_data, f, indent=2)
    except Exception as e:
        print(f"Warning: Failed to write {output_path}: {e}", file=sys.stderr)

    return exit_code, report_data


def print_summary(report: Dict[str, Any]) -> None:
    """Prints concise human-readable summary to stdout."""
    status = report.get("gate_status", "UNKNOWN")
    summary = report.get("summary", {})
    prov = report.get("provenance_check", {})
    intent = report.get("intent_check", {})
    secrets = report.get("secret_detection_check", {})
    violations = report.get("violations", [])

    print("\n" + "=" * 60)
    print(f"               ACCOUNTABILITY GATE: {status}")
    print("=" * 60)
    print(f"1. Provenance Check: {prov.get('status', 'N/A')}")
    print(f"   - Commits Inspected: {summary.get('commits_inspected', 0)}")
    print(f"   - Valid Trailers:    {summary.get('valid_trailers', 0)}")
    for c in prov.get("commits", []):
        tag = "VALID" if c.get("valid_trailer") else "INVALID"
        trailer = c.get("assisted_by") or "MISSING"
        print(f"     [{c.get('short_sha')}] {c.get('subject')} (Trailer: {trailer}) -> {tag}")

    print(f"\n2. Intent Check: {intent.get('status', 'N/A')}")
    print(f"   - Linked Issue: {intent.get('linked_issue') or 'None'}")
    if intent.get("keyword"):
        print(f"   - Keyword:      {intent.get('keyword')}")

    print(f"\n3. Secret Detection: {secrets.get('status', 'N/A')}")
    print(f"   - Report:   {secrets.get('report_path')}")
    print(f"   - Findings: {secrets.get('findings_count', 0)}")

    if violations:
        print(f"\nViolations ({len(violations)}):")
        for idx, v in enumerate(violations, 1):
            print(f"   [{idx}] {v}")
    else:
        print("\nViolations: None")

    print("=" * 60 + "\n")


def main() -> None:
    parser = argparse.ArgumentParser(description="Accountability Gate for GitLab DevSecOps pipelines")
    parser.add_argument("--base", help="Base commit SHA or ref for merge request comparison")
    parser.add_argument("--head", default=None, help="Head commit SHA or ref (default: HEAD / CI_COMMIT_SHA)")
    parser.add_argument("--description", help="Merge request description content")
    parser.add_argument(
        "--secret-report",
        default="gl-secret-detection-report.json",
        help="Path to GitLab Secret Detection JSON report",
    )
    parser.add_argument(
        "--require-secret-report",
        action="store_true",
        help="Fail gate if secret detection report is absent",
    )
    parser.add_argument(
        "--output",
        default="gate_report.json",
        help="Path for JSON report artifact output",
    )
    parser.add_argument("--repo-dir", default=".", help="Repository path (default: current directory)")

    args = parser.parse_args()

    exit_code, report = run_gate(
        base=args.base,
        head=args.head,
        description=args.description,
        secret_report=args.secret_report,
        require_secret_report=args.require_secret_report,
        output_path=args.output,
        repo_dir=args.repo_dir,
    )

    print_summary(report)
    sys.exit(exit_code)


if __name__ == "__main__":
    main()

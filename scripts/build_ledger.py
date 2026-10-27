#!/usr/bin/env python3
"""
Accountability & Provenance Ledger Builder for GitLab Pages.

Parses repository git commit history and gate_report.json to generate a static
HTML dashboard representing the continuous Accountability Ledger.
Published via GitLab Pages to the 'staging' environment.
Zero external CSS/JS dependencies (fully self-contained).
"""

import argparse
import html
import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple


def parse_trailer(msg: str, key: str = "Assisted-by") -> Optional[str]:
    """Extracts trailer from commit message body."""
    import re

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
            return None
        k = match.group(1).lower()
        v = match.group(2).strip()
        trailers[k] = v

    val = trailers.get(key.lower())
    return val if (val is not None and len(val) > 0) else None


def resolve_baseline_sha(
    cli_baseline: Optional[str] = None,
    repo_dir: str = ".",
) -> Tuple[Optional[str], Optional[Set[str]]]:
    """
    Resolves baseline commit SHA from CLI argument or ACCOUNTABILITY_BASELINE_SHA env var.
    Returns (resolved_full_sha, set_of_ancestor_and_self_shas).
    Commits at or before this SHA are grandfathered (pre-contract).
    """
    raw_val = cli_baseline or os.environ.get("ACCOUNTABILITY_BASELINE_SHA")
    if not raw_val or not raw_val.strip():
        return None, None

    raw_val = raw_val.strip()
    try:
        res = subprocess.run(
            ["git", "rev-parse", "--verify", f"{raw_val}^{{commit}}"],
            cwd=repo_dir,
            capture_output=True,
            text=True,
            check=False,
        )
        if res.returncode != 0:
            return raw_val, None

        full_baseline = res.stdout.strip()
        rev_res = subprocess.run(
            ["git", "rev-list", full_baseline],
            cwd=repo_dir,
            capture_output=True,
            text=True,
            check=False,
        )
        if rev_res.returncode == 0:
            ancestors = set(line.strip() for line in rev_res.stdout.splitlines() if line.strip())
            return full_baseline, ancestors

        return full_baseline, {full_baseline}
    except Exception:
        return raw_val, None


def get_commit_history(
    repo_dir: str = ".",
    max_count: int = 50,
    baseline_sha: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """Retrieves commit history with provenance trailers and classification from git log."""
    _, grandfathered_shas = resolve_baseline_sha(baseline_sha, repo_dir=repo_dir)

    # Format: SHA | Author Name | Author Email | Date (ISO) | Subject | Parents (space-separated)
    fmt = "%H%x1f%an%x1f%ae%x1f%aI%x1f%s%x1f%P"
    cmd = ["git", "log", f"--max-count={max_count}", f"--format={fmt}"]

    try:
        res = subprocess.run(cmd, cwd=repo_dir, capture_output=True, text=True, check=False)
        if res.returncode != 0:
            print(f"Warning: git log failed: {res.stderr.strip()}", file=sys.stderr)
            return []
    except Exception as e:
        print(f"Warning: Failed to execute git log: {e}", file=sys.stderr)
        return []

    commits: List[Dict[str, Any]] = []
    lines = [line.strip() for line in res.stdout.splitlines() if line.strip()]

    for line in lines:
        parts = line.split("\x1f")
        if len(parts) < 5:
            continue
        sha, author_name, author_email, date_iso, subject = parts[0], parts[1], parts[2], parts[3], parts[4]
        parents_str = parts[5].strip() if len(parts) > 5 else ""
        parent_list = [p for p in parents_str.split() if p]

        # Fetch full commit message to inspect trailers reliably
        msg_res = subprocess.run(
            ["git", "log", "-1", "--format=%B", sha],
            cwd=repo_dir,
            capture_output=True,
            text=True,
            check=False,
        )
        full_msg = msg_res.stdout if msg_res.returncode == 0 else subject
        trailer = parse_trailer(full_msg, "Assisted-by")

        # Check merge commit & grandfathered status
        is_merge = len(parent_list) > 1
        is_grandfathered = bool(grandfathered_shas and sha in grandfathered_shas)

        # Determine provenance classification
        if is_merge:
            category = "Merge (excluded)"
            badge_class = "badge-neutral"
            in_scope = False
            is_verified = False
        elif is_grandfathered:
            category = "Grandfathered (pre-contract)"
            badge_class = "badge-neutral"
            in_scope = False
            is_verified = False
        else:
            in_scope = True
            is_verified = trailer is not None and len(trailer.strip()) > 0
            if is_verified:
                if trailer.lower() == "none":
                    category = "Human Only"
                    badge_class = "badge-human"
                else:
                    category = f"AI-Assisted ({trailer})"
                    badge_class = "badge-ai"
            else:
                category = "Missing Provenance"
                badge_class = "badge-unverified"

        commits.append({
            "sha": sha,
            "short_sha": sha[:8],
            "author_name": author_name,
            "author_email": author_email,
            "date_iso": date_iso,
            "subject": subject,
            "trailer": trailer,
            "category": category,
            "badge_class": badge_class,
            "is_verified": is_verified,
            "is_merge": is_merge,
            "is_grandfathered": is_grandfathered,
            "in_scope": in_scope,
        })

    return commits


def load_gate_report(report_path: str) -> Optional[Dict[str, Any]]:
    """Loads gate_report.json if present. Returns a structured invalid dictionary if malformed."""
    if not os.path.exists(report_path):
        return None
    try:
        with open(report_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        if not isinstance(data, dict) or "gate_status" not in data:
            return {
                "gate_status": "INVALID_REPORT",
                "summary": {"total_violations": 1, "linked_issue": "None"},
                "violations": ["Invalid gate report structure: missing 'gate_status' field."],
            }
        return data
    except Exception as e:
        return {
            "gate_status": "INVALID_REPORT",
            "summary": {"total_violations": 1, "linked_issue": "None"},
            "violations": [f"Malformed gate report JSON: {e}"],
        }


def generate_html(
    commits: List[Dict[str, Any]],
    gate_report: Optional[Dict[str, Any]],
    project_title: str = "AI Accountability Ledger",
    environment: str = "staging",
) -> str:
    """Generates standalone responsive HTML for the Accountability Ledger."""
    now_utc = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")

    # Metrics calculation
    total_commits = len(commits)
    merge_count = sum(1 for c in commits if c.get("is_merge"))
    grandfathered_count = sum(1 for c in commits if c.get("is_grandfathered"))

    in_scope_commits = [c for c in commits if not c.get("is_merge") and not c.get("is_grandfathered")]
    in_scope_count = len(in_scope_commits)

    verified_count = sum(1 for c in in_scope_commits if c.get("is_verified"))
    ai_assisted_count = sum(1 for c in in_scope_commits if c.get("is_verified") and c.get("trailer") and c["trailer"].lower() != "none")
    human_only_count = sum(1 for c in in_scope_commits if c.get("is_verified") and c.get("trailer") and c["trailer"].lower() == "none")

    if total_commits == 0:
        compliance_rate = 0.0
    elif in_scope_count == 0:
        compliance_rate = 100.0
    else:
        compliance_rate = (verified_count / in_scope_count * 100.0)

    # Gate info
    gate_status = "NOT AVAILABLE"
    gate_badge_class = "badge-neutral"
    linked_issue = "None"
    violations_count = 0
    violations: List[str] = []

    if gate_report is not None:
        raw_status = gate_report.get("gate_status", "UNKNOWN")
        if raw_status == "PASSED":
            gate_status = "PASSED"
            gate_badge_class = "badge-pass"
        elif raw_status == "FAILED":
            gate_status = "FAILED"
            gate_badge_class = "badge-fail"
        elif raw_status == "INVALID_REPORT":
            gate_status = "INVALID REPORT"
            gate_badge_class = "badge-fail"
        else:
            gate_status = str(raw_status)
            gate_badge_class = "badge-neutral"

        summary = gate_report.get("summary", {})
        intent = gate_report.get("intent_check", {})
        if intent.get("status") == "NOT_APPLICABLE":
            linked_issue = "N/A (Push Mode)"
        else:
            linked_issue = summary.get("linked_issue") or "None"
        violations = gate_report.get("violations", [])
        violations_count = summary.get("total_violations", len(violations))

    violations_html = ""
    if violations:
        items = "\n".join(f"<li>{html.escape(str(v))}</li>" for v in violations)
        violations_html = f"""
    <div class="violations-card">
      <div class="violations-title">Reported Gate Violations ({len(violations)})</div>
      <ul class="violations-list">
        {items}
      </ul>
    </div>
    """

    # Build rows
    rows_html = []
    for c in commits:
        if c.get("is_merge"):
            trailer_display = f"Assisted-by: {c['trailer']}" if c.get("trailer") else "N/A (Merge commit)"
        elif c.get("is_grandfathered"):
            trailer_display = f"Assisted-by: {c['trailer']}" if c.get("trailer") else "N/A (Pre-contract baseline)"
        else:
            trailer_display = f"Assisted-by: {c.get('trailer') or 'MISSING'}"

        rows_html.append(f"""
        <tr>
          <td class="font-mono">
            <span class="commit-hash">{html.escape(c['short_sha'])}</span>
          </td>
          <td class="commit-subject">{html.escape(c['subject'])}</td>
          <td>{html.escape(c['author_name'])}</td>
          <td class="text-muted">{html.escape(c['date_iso'][:10])}</td>
          <td>
            <span class="badge {c['badge_class']}">{html.escape(c['category'])}</span>
          </td>
          <td>
            <code class="trailer-code">{html.escape(trailer_display)}</code>
          </td>
        </tr>
        """)

    table_body = "\n".join(rows_html) if rows_html else "<tr><td colspan='6' class='text-center'>No commits found.</td></tr>"

    html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{html.escape(project_title)} - GitLab Pages Staging</title>
  <style>
    :root {{
      --bg: #0d1117;
      --card-bg: #161b22;
      --border: #30363d;
      --text: #c9d1d9;
      --text-bright: #f0f6fc;
      --text-muted: #8b949e;
      --accent: #58a6ff;
      --green: #238636;
      --green-light: #2ea043;
      --red: #da3633;
      --purple: #8957e5;
      --blue: #1f6feb;
    }}
    * {{ box-sizing: border-box; margin: 0; padding: 0; }}
    body {{
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Helvetica, Arial, sans-serif;
      background-color: var(--bg);
      color: var(--text);
      line-height: 1.6;
      padding: 24px;
    }}
    .container {{
      max-width: 1200px;
      margin: 0 auto;
    }}
    header {{
      display: flex;
      justify-content: space-between;
      align-items: center;
      padding-bottom: 20px;
      border-bottom: 1px solid var(--border);
      margin-bottom: 24px;
      flex-wrap: wrap;
      gap: 16px;
    }}
    .title-group h1 {{
      font-size: 26px;
      color: var(--text-bright);
      display: flex;
      align-items: center;
      gap: 12px;
    }}
    .subtitle {{
      color: var(--text-muted);
      font-size: 14px;
      margin-top: 4px;
    }}
    .env-badge {{
      display: inline-block;
      padding: 4px 10px;
      border-radius: 20px;
      font-size: 12px;
      font-weight: 600;
      text-transform: uppercase;
      letter-spacing: 0.5px;
      background: rgba(88, 166, 255, 0.15);
      color: var(--accent);
      border: 1px solid rgba(88, 166, 255, 0.3);
    }}
    .stats-grid {{
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
      gap: 16px;
      margin-bottom: 28px;
    }}
    .stat-card {{
      background: var(--card-bg);
      border: 1px solid var(--border);
      border-radius: 8px;
      padding: 16px;
    }}
    .stat-label {{
      font-size: 13px;
      color: var(--text-muted);
      margin-bottom: 6px;
    }}
    .stat-value {{
      font-size: 24px;
      font-weight: 700;
      color: var(--text-bright);
    }}
    .stat-sub {{
      font-size: 12px;
      color: var(--text-muted);
      margin-top: 4px;
    }}
    .card {{
      background: var(--card-bg);
      border: 1px solid var(--border);
      border-radius: 8px;
      overflow: hidden;
      margin-bottom: 28px;
    }}
    .card-header {{
      padding: 16px 20px;
      border-bottom: 1px solid var(--border);
      display: flex;
      justify-content: space-between;
      align-items: center;
      background: rgba(255, 255, 255, 0.02);
    }}
    .card-header h2 {{
      font-size: 18px;
      color: var(--text-bright);
    }}
    table {{
      width: 100%;
      border-collapse: collapse;
      text-align: left;
      font-size: 14px;
    }}
    th {{
      padding: 12px 16px;
      background: rgba(255, 255, 255, 0.03);
      color: var(--text-muted);
      font-weight: 600;
      border-bottom: 1px solid var(--border);
    }}
    td {{
      padding: 12px 16px;
      border-bottom: 1px solid var(--border);
    }}
    tr:last-child td {{
      border-bottom: none;
    }}
    tr:hover {{
      background: rgba(255, 255, 255, 0.02);
    }}
    .font-mono {{ font-family: ui-monospace, SFMono-Regular, "SF Mono", Menlo, Consolas, monospace; }}
    .commit-hash {{
      background: rgba(255, 255, 255, 0.08);
      padding: 2px 6px;
      border-radius: 4px;
      color: var(--accent);
      font-size: 13px;
    }}
    .commit-subject {{
      color: var(--text-bright);
      font-weight: 500;
    }}
    .trailer-code {{
      font-size: 12px;
      background: rgba(0, 0, 0, 0.3);
      padding: 2px 6px;
      border-radius: 4px;
      border: 1px solid var(--border);
    }}
    .badge {{
      display: inline-block;
      padding: 3px 8px;
      border-radius: 12px;
      font-size: 12px;
      font-weight: 600;
    }}
    .badge-pass {{ background: rgba(46, 160, 67, 0.2); color: #3fb950; border: 1px solid rgba(46, 160, 67, 0.4); }}
    .badge-fail {{ background: rgba(218, 54, 51, 0.2); color: #f85149; border: 1px solid rgba(218, 54, 51, 0.4); }}
    .badge-neutral {{ background: rgba(139, 148, 158, 0.2); color: #8b949e; border: 1px solid rgba(139, 148, 158, 0.4); }}
    .badge-ai {{ background: rgba(137, 87, 229, 0.2); color: #a371f7; border: 1px solid rgba(137, 87, 229, 0.4); }}
    .badge-human {{ background: rgba(31, 111, 235, 0.2); color: #58a6ff; border: 1px solid rgba(31, 111, 235, 0.4); }}
    .badge-unverified {{ background: rgba(218, 54, 51, 0.2); color: #f85149; border: 1px solid rgba(218, 54, 51, 0.4); }}
    .disclaimer-card {{
      background: rgba(88, 166, 255, 0.05);
      border: 1px solid rgba(88, 166, 255, 0.2);
      border-radius: 8px;
      padding: 16px 20px;
      font-size: 13px;
      color: var(--text-muted);
      margin-bottom: 24px;
    }}
    .disclaimer-card strong {{
      color: var(--accent);
    }}
    .violations-card {{
      background: rgba(218, 54, 51, 0.1);
      border: 1px solid rgba(218, 54, 51, 0.4);
      border-radius: 8px;
      padding: 16px 20px;
      margin-bottom: 24px;
    }}
    .violations-title {{
      color: #f85149;
      font-weight: 700;
      margin-bottom: 8px;
      font-size: 15px;
    }}
    .violations-list {{
      margin-left: 20px;
      color: var(--text);
      font-size: 13px;
    }}
    .violations-list li {{
      margin-bottom: 4px;
    }}
    footer {{
      text-align: center;
      color: var(--text-muted);
      font-size: 12px;
      padding-top: 16px;
      border-top: 1px solid var(--border);
    }}
  </style>
</head>
<body>
  <div class="container">
    <header>
      <div class="title-group">
        <h1>
          <span>{html.escape(project_title)}</span>
          <span class="env-badge">{html.escape(environment)}</span>
        </h1>
        <div class="subtitle">GitLab Transcend Hackathon &bull; DevSecOps Lifecycle Governance</div>
      </div>
      <div>
        <span class="stat-sub">Generated: {html.escape(now_utc)}</span>
      </div>
    </header>

    <div class="stats-grid">
      <div class="stat-card">
        <div class="stat-label">Pipeline Gate Status</div>
        <div class="stat-value">
          <span class="badge {gate_badge_class}">{html.escape(gate_status)}</span>
        </div>
        <div class="stat-sub">Linked Issue: {html.escape(linked_issue)} &bull; {violations_count} violation(s)</div>
      </div>

      <div class="stat-card">
        <div class="stat-label">Provenance Compliance</div>
        <div class="stat-value">{compliance_rate:.1f}%</div>
        <div class="stat-sub">{verified_count} of {in_scope_count} evaluated commits compliant</div>
      </div>

      <div class="stat-card">
        <div class="stat-label">AI-Assisted Commits</div>
        <div class="stat-value" style="color: var(--purple);">{ai_assisted_count}</div>
        <div class="stat-sub">Carrying tool/agent trailer</div>
      </div>

      <div class="stat-card">
        <div class="stat-label">Human-Only Commits</div>
        <div class="stat-value" style="color: var(--accent);">{human_only_count}</div>
        <div class="stat-sub">Assisted-by: none</div>
      </div>

      <div class="stat-card">
        <div class="stat-label">Grandfathered Commits</div>
        <div class="stat-value" style="color: var(--text-muted);">{grandfathered_count}</div>
        <div class="stat-sub">Grandfathered (pre-contract)</div>
      </div>

      <div class="stat-card">
        <div class="stat-label">Merge Commits</div>
        <div class="stat-value" style="color: var(--text-muted);">{merge_count}</div>
        <div class="stat-sub">Merge (excluded)</div>
      </div>
    </div>

    {violations_html}

    <div class="disclaimer-card">
      <strong>Honest Limitation &amp; Governance Contract:</strong> AI origin cannot be reliably detected retrospectively in legacy commits without metadata. This pipeline establishes an enforced provenance contract going forward: every change must carry an <code>Assisted-by:</code> trailer and explicit issue intent linkage (<code>Closes #&lt;id&gt;</code>) enforced at the merge gate.
    </div>

    <div class="card">
      <div class="card-header">
        <h2>Continuous Provenance Ledger</h2>
        <span class="stat-sub">{total_commits} commits indexed ({in_scope_count} evaluated &bull; {grandfathered_count} grandfathered &bull; {merge_count} excluded)</span>
      </div>
      <div style="overflow-x: auto;">
        <table>
          <thead>
            <tr>
              <th>Commit</th>
              <th>Subject</th>
              <th>Author</th>
              <th>Date</th>
              <th>Classification</th>
              <th>Git Trailer</th>
            </tr>
          </thead>
          <tbody>
            {table_body}
          </tbody>
        </table>
      </div>
    </div>

    <footer>
      <p>GitLab Duo Agent Platform &bull; Life After Code Hackathon Submission &bull; Powered by GitLab Pages &amp; CI/CD</p>
    </footer>
  </div>
</body>
</html>
"""
    return html_content


def build_ledger(
    output_dir: str = "public",
    gate_report_path: str = "gate_report.json",
    repo_dir: str = ".",
    project_title: str = "AI Accountability Ledger",
    environment: str = "staging",
    baseline_sha: Optional[str] = None,
) -> Path:
    """Builds the static Accountability Ledger page into output_dir/index.html."""
    out_path = Path(output_dir)
    out_path.mkdir(parents=True, exist_ok=True)

    commits = get_commit_history(repo_dir=repo_dir, baseline_sha=baseline_sha)
    gate_report = load_gate_report(gate_report_path)

    html_page = generate_html(
        commits=commits,
        gate_report=gate_report,
        project_title=project_title,
        environment=environment,
    )

    index_file = out_path / "index.html"
    index_file.write_text(html_page, encoding="utf-8")
    print(f"Accountability Ledger successfully built: {index_file} ({len(commits)} commits indexed)")
    return index_file


def main() -> None:
    parser = argparse.ArgumentParser(description="Build static Accountability Ledger for GitLab Pages")
    parser.add_argument("--output-dir", default="public", help="Output directory for static site (default: public)")
    parser.add_argument(
        "--gate-report",
        default="gate_report.json",
        help="Path to gate_report.json artifact (default: gate_report.json)",
    )
    parser.add_argument("--repo-dir", default=".", help="Repository directory (default: current directory)")
    parser.add_argument(
        "--baseline-sha",
        default=None,
        help="Commit SHA at or before which commits are grandfathered (defaults to ACCOUNTABILITY_BASELINE_SHA env var)",
    )
    parser.add_argument(
        "--title",
        default="AI Accountability Ledger",
        help="Page title for the dashboard",
    )
    parser.add_argument(
        "--environment",
        default="staging",
        help="Deployment environment name (default: staging)",
    )

    args = parser.parse_args()
    build_ledger(
        output_dir=args.output_dir,
        gate_report_path=args.gate_report,
        repo_dir=args.repo_dir,
        project_title=args.title,
        environment=args.environment,
        baseline_sha=args.baseline_sha,
    )


if __name__ == "__main__":
    main()

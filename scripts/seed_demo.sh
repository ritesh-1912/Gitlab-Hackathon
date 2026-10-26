#!/usr/bin/env bash
# ==============================================================================
# scripts/seed_demo.sh
# Prepares 3 local Git branches for GitLab Transcend Hackathon live/recorded demo.
# Note: Pushes NOTHING automatically. Prints manual push and MR steps.
# ==============================================================================

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT"

# Ensure we are in a clean git repo
if ! git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  echo "Error: Must run inside a Git repository." >&2
  exit 1
fi

CURRENT_BRANCH="$(git rev-parse --abbrev-ref HEAD)"
if [ "$CURRENT_BRANCH" != "main" ]; then
  echo "Switching to main branch..."
  git checkout main
fi

echo "===================================================================="
echo "          SEEDING DEMO SCENARIOS FOR GITLAB HACKATHON               "
echo "===================================================================="

# ------------------------------------------------------------------------------
# Scenario A: Clean Feature MR (Passes all checks, deploys to Ledger)
# ------------------------------------------------------------------------------
echo "--> [1/3] Preparing branch: demo/scenario-a-clean..."
git branch -D demo/scenario-a-clean 2>/dev/null || true
git checkout -b demo/scenario-a-clean main

# Add a clean inventory summary endpoint in src/app.py before 'return app'
python3 -c '
with open("src/app.py", "r") as f:
    code = f.read()

summary_endpoint = """
    @app.route("/inventory/summary", methods=["GET"])
    def inventory_summary():
        total_qty = sum(item["quantity"] for item in items)
        return jsonify({"total_items": len(items), "total_quantity": total_qty}), 200
"""

if "/inventory/summary" not in code:
    code = code.replace("    return app", summary_endpoint + "\n    return app")
    with open("src/app.py", "w") as f:
        f.write(code)
'

# Add unit test in tests/test_app.py
cat << 'EOF' >> tests/test_app.py

def test_inventory_summary_endpoint(client):
    response = client.get("/inventory/summary")
    assert response.status_code == 200
    data = response.get_json()
    assert data["total_items"] >= 2
    assert data["total_quantity"] > 0
EOF

git add src/app.py tests/test_app.py
git commit -m "feat: add inventory summary endpoint

Implements aggregated inventory summary calculation.

Assisted-by: gitlab-duo"

echo "    Branch demo/scenario-a-clean created successfully."

# ------------------------------------------------------------------------------
# Scenario B: Bad MR (Missing Trailer, Scope Creep, and Fake Dummy Secret)
# ------------------------------------------------------------------------------
echo "--> [2/3] Preparing branch: demo/scenario-b-bad-gate..."
git checkout main
git branch -D demo/scenario-b-bad-gate 2>/dev/null || true
git checkout -b demo/scenario-b-bad-gate main

# Add fake secret to src/app.py (strictly for Secret Detection demo, never merged)
python3 -c '
with open("src/app.py", "r") as f:
    code = f.read()

# AWS Access Key pattern matching Gitleaks / GitLab Secret Detection regex
secret_code = """
# FAKE DUMMY CREDENTIAL FOR SECRET DETECTION VERIFICATION ONLY - DO NOT USE
FAKE_DEMO_AWS_KEY = "AKIAIOSFODNN7EXAMPLE"
"""

if "FAKE_DEMO_AWS_KEY" not in code:
    code = secret_code + code
    with open("src/app.py", "w") as f:
        f.write(code)
'

# Add an unrelated scope-creep file
cat << 'EOF' > src/unrelated_admin_tool.py
"""
Unrelated administrative script introduced without issue intent linkage (Scope Creep).
"""
def secret_backdoor():
    pass
EOF

git add src/app.py src/unrelated_admin_tool.py
# Intentionally commit with NO trailer
git commit -m "wip: add admin tool and demo credentials"

echo "    Branch demo/scenario-b-bad-gate created successfully."

# ------------------------------------------------------------------------------
# Scenario C: Broken Release (Fails Staging Healthcheck Smoke Test)
# ------------------------------------------------------------------------------
echo "--> [3/3] Preparing branch: demo/scenario-c-bad-healthcheck..."
git checkout main
git branch -D demo/scenario-c-bad-healthcheck 2>/dev/null || true
git checkout -b demo/scenario-c-bad-healthcheck main

# Modify /health to simulate regression
python3 -c '
with open("src/app.py", "r") as f:
    code = f.read()

old_health = """    @app.route("/health", methods=["GET"])
    def health():
        return jsonify({"status": "healthy", "service": "inventory-api"}), 200"""

bad_health = """    @app.route("/health", methods=["GET"])
    def health():
        # Regression: database connection pool exhausted
        return jsonify({
            "status": "degraded",
            "error": "Unhandled DBConnectionPoolTimeout: pool size 0 exhausted"
        }), 500"""

if old_health in code:
    code = code.replace(old_health, bad_health)
    with open("src/app.py", "w") as f:
        f.write(code)
'

git add src/app.py
git commit -m "fix(db): adjust connection pooling timeout

Assisted-by: gitlab-duo"

echo "    Branch demo/scenario-c-bad-healthcheck created successfully."

# Switch back to main
git checkout main

echo ""
echo "===================================================================="
echo "          DEMO BRANCHES READY FOR PUSH (MANUAL STEPS)               "
echo "===================================================================="
echo ""
echo "When ready to record or present, execute the following commands:"
echo ""
echo "1. SCENARIO A (Clean Pass):"
echo "   git push -u origin demo/scenario-a-clean"
echo "   Create MR on GitLab: 'feat: add inventory summary endpoint'"
echo "   MR Description: 'Implements inventory summary endpoint. Closes #1'"
echo "   Expected Result: Tests pass, Gate passes, Pages Ledger updates."
echo ""
echo "2. SCENARIO B (Gate & Secret Catch):"
echo "   git push -u origin demo/scenario-b-bad-gate"
echo "   Create MR on GitLab: 'wip: add admin tool'"
echo "   MR Description: 'Adds admin tool without linked issue.'"
echo "   Expected Result: Gate fails (missing trailer), Secret Detection flags fake key."
echo "   Accountability Card recommends: REJECT."
echo ""
echo "3. SCENARIO C (Incident & Root Cause Trace):"
echo "   git push -u origin demo/scenario-c-bad-healthcheck"
echo "   Merge into main to trigger deploy."
echo "   Expected Result: Staging healthcheck fails."
echo "   Create Incident Issue using .gitlab/issue_templates/incident.md and mention @incident-trace."
echo "   Flow outputs: 'git revert <sha> --no-edit' to remediate."
echo "===================================================================="

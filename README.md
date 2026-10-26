# <PROJECT_NAME>: AI Accountability Pipeline

> **GitLab Transcend Hackathon ("Life After Code") Submission**  
> Automated DevSecOps Lifecycle Governance & Provenance Tracing with the **GitLab Duo Agent Platform**.

---

## 💡 Overview

Generative AI solved code authoring. Engineering teams now ship code faster than ever, but software delivery has encountered a new bottleneck: **governance, traceability, and incident triage**.

When an incident occurs in production, most teams cannot answer:
1. **Where did this code originate?** (Which developer, AI tool, or agent authored it?)
2. **What was it intended to do?** (Which requirement or acceptance criteria justified it?)
3. **Who is responsible?** (Can we trace a failed release back to its prompt origin and immediately remediate?)

**`<PROJECT_NAME>`** closes this gap. It is an end-to-end DevSecOps pipeline and GitLab Duo custom flow suite that makes every change carry cryptographic/metadata provenance (`Assisted-by:` trailers) and explicit intent linkage (`Closes #<id>`), gates merges automatically via CI, maintains a live **Accountability Ledger** on GitLab Pages, and equips Duo agents to triage intent, evaluate review risk, and trace release incidents back to their source.

---

## ⚠️ Honest Limitation & Governance Scope

> [!IMPORTANT]
> **Provenance Contract Applies Going Forward**: AI origin cannot be reliably detected retrospectively in legacy Git commits without metadata. Rather than guessing with unreliable statistical heuristics, `<PROJECT_NAME>` establishes an **enforceable governance contract going forward**:
> - Every commit must declare its provenance trailer (`Assisted-by: <tool|agent|none>`).
> - Every MR must link to an intent issue (`Closes #<id>` or `Fixes #<id>`).
> - Merge gates block non-compliant commits from reaching the default branch.

---

## 🏛️ Architecture & Lifecycle Coverage

`<PROJECT_NAME>` automates 8 distinct DevSecOps lifecycle stages under **Supervised Autonomy**—agents perform multi-step analysis, but the human retains final authority (*"Advisory only: a human decides"*).

```mermaid
flowchart TD
    subgraph Plan["1. Plan & Scope"]
        Issue["GitLab Issue #N"] -->|"@intent-agent mention"| Flow1["Flow 1: Intent Definition<br/>(Acceptance criteria & out-of-scope)"]
    end

    subgraph CreateVerify["2. Create, Verify & Secure"]
        Dev["Developer / Duo Agent"] -->|"Commit with Assisted-by: trailer"| MR["Merge Request (Closes #N)"]
        MR -->|"Pipeline Trigger"| CI["GitLab CI Pipeline"]
        CI -->|"Pytest"| TestJob["test (Unit Tests)"]
        CI -->|"SAST & Secret Detection"| SecJob["security (gl-secret-detection-report.json)"]
        SecJob --> GateJob["accountability-gate<br/>(Validates trailers, intent, secrets)"]
        MR -->|"@accountability-card mention"| Flow2["Flow 2: Accountability Card<br/>(Risk, intent match, scope creep)"]
    end

    subgraph ReleaseGovern["3. Release & Govern"]
        GateJob -->|"Merge to main"| DeployJob["pages (Deploy to Staging)"]
        DeployJob --> Ledger["Accountability Ledger<br/>(GitLab Pages static site)"]
    end

    subgraph MonitorRemediate["4. Monitor & Remediate"]
        DeployJob --> SmokeJob["staging-healthcheck<br/>(In-process smoke test)"]
        SmokeJob -->|"On Failure"| IncIssue["Incident Issue"]
        IncIssue -->|"@incident-trace mention"| Flow3["Flow 3: Incident Trace<br/>(Traces MR, prompt origin, outputs git revert)"]
    end
```

### DevSecOps Lifecycle Stages Covered

| Lifecycle Stage | Implementation in `<PROJECT_NAME>` | Duo Agent Platform Role |
| :--- | :--- | :--- |
| **Plan** | Flow 1: Intent Definition | Agent generates acceptance criteria, checklists, and out-of-scope boundaries on issue creation. |
| **Create** | Provenance Trailers & Intent Links | Enforces `Assisted-by: <tool|none>` commit trailers and `Closes #N` MR intent links. |
| **Verify** | Pytest Suite & Flow 2 Card | Unit tests + Duo Review Card evaluating intent match and scope creep. |
| **Secure** | GitLab SAST & Secret Detection | Scans merge requests; Gate parses report and halts on exposed credentials. |
| **Release** | GitLab Pages Deployment | Pipeline registers `staging` environment and publishes the latest build. |
| **Govern** | Accountability Gate & Ledger | Automated merge gate + static HTML Accountability Ledger published to Pages. |
| **Monitor** | In-Process Staging Healthcheck | Smoke test verifying `/health` and service endpoints post-deployment. |
| **Remediate** | Flow 3: Incident Trace | Traces failed releases to culprit commits and outputs exact `git revert` commands. |

---

## 📂 Repository Structure

```
<PROJECT_NAME>/
├── .gitlab-ci.yml                 # 5-stage pipeline: test -> security -> gate -> deploy -> healthcheck
├── .gitlab/
│   └── issue_templates/
│       └── incident.md            # Telemetry issue template for post-incident triage
├── LICENSE                        # MIT License (<YOUR NAME>)
├── README.md                      # Complete architecture & setup documentation
├── DEMO.md                        # Under-3-minute video recording walkthrough script
├── DEVPOST.md                     # Official Devpost submission write-up
├── VIDEO_SCRIPT.md                # Word-for-word timed recording script (< 2:45)
├── docs/                          # Official GitLab Duo Flow specs & schemas (saved locally)
│   ├── README.md                  # Index of references and authoring rules
│   ├── custom_flows_schema.md     # Flow Registry v1 schema
│   ├── custom_flows.md            # Execution mechanics
│   ├── triggers.md                # Triggers documentation
│   ├── flow_registry_v1_spec.md   # Raw Flow Registry v1 specification
│   └── official_example_flow.md   # GitLab multi-agent flow blog post & sample
├── flows/                         # GitLab Duo Custom Flows (v1 Ambient Schema)
│   ├── tracer-bullet.yml          # Minimal 15-line flow to verify trigger & issue note
│   ├── intent.yml                 # Flow 1: Intent, acceptance criteria & out-of-scope list
│   ├── accountability-card.yml    # Flow 2: Origin, diff, scope creep & risk review card
│   └── incident-trace.yml         # Flow 3: Post-incident telemetry trace & git revert output
├── scripts/
│   ├── accountability_gate.py     # CI gate: validates commit trailers, intent, and secrets
│   ├── build_ledger.py            # Generates static HTML Accountability Ledger for Pages
│   ├── smoke_test.py              # In-process staging smoke test runner (with failure mode)
│   └── seed_demo.sh               # Local branch preparation for Demo Scenarios A, B, and C
├── src/
│   ├── app.py                     # Minimal Inventory Microservice (<100 lines Python/Flask)
│   └── requirements.txt           # Minimal dependencies (Flask, pytest, requests)
└── tests/
    ├── test_app.py                # Unit tests for Flask microservice endpoints
    ├── test_accountability_gate.py# 32 unit & integration tests for gate logic & push mode
    └── test_ledger_and_smoke.py   # 12 tests for ledger generation, XSS escaping, smoke tests
```

---

## 🚀 Setup & Local Execution

### 1. Prerequisites
- Python 3.11+
- Git 2.30+

### 2. Local Installation
```bash
# Clone the repository
git clone https://github.com/ritesh-1912/Gitlab-Hackathon.git
cd Gitlab-Hackathon

# Install test dependencies
pip install -r src/requirements.txt

# Run the full automated test suite (49 tests)
python3 -m pytest -v
```

### 3. Running Gate & Ledger Locally
```bash
# Test the Accountability Gate in push mode
python3 scripts/accountability_gate.py --mode push

# Generate the Accountability Ledger locally into public/index.html
python3 scripts/build_ledger.py --output-dir public

# Run the in-process healthcheck smoke test
python3 scripts/smoke_test.py

# Simulate an unhealthy release
python3 scripts/smoke_test.py --fail-on-purpose
```

---

## 🦊 GitLab Configuration Guide

### 1. Project & Merge Settings
1. Create a **Public** project on GitLab named `<PROJECT_NAME>`.
2. Navigate to **Settings > Merge requests**:
   - Set **Merge method** to **Merge commit** (preserves individual commit history and `Assisted-by:` trailers in `main`).
3. Navigate to **Deploy > Pages**:
   - Ensure Pages access is set to **Everyone** so the public Accountability Ledger is accessible.

### 2. Register GitLab Duo Custom Flows
In GitLab, navigate to **Automate > AI Agents & Flows** (or **Settings > GitLab Duo > Flows**):
1. **Tracer Bullet** (`flows/tracer-bullet.yml`): Register and add **Mention** trigger.
2. **Intent Flow** (`flows/intent.yml`): Register as `intent-agent` and add **Mention** trigger.
3. **Accountability Card** (`flows/accountability-card.yml`): Register as `accountability-card` and add **Mention** trigger.
4. **Incident Trace** (`flows/incident-trace.yml`): Register as `incident-trace` and add **Mention** trigger.

---

## 🎬 Running Demo Scenarios

Run the seeding script to prepare the three demo branches locally:
```bash
./scripts/seed_demo.sh
```

### Scenario A: Clean Feature MR (Passes & Deploys)
1. Push branch: `git push -u origin demo/scenario-a-clean`.
2. Open MR with description: `Implements inventory summary endpoint. Closes #1`.
3. Mention `@accountability-card` in the MR comment.
4. **Result**: All tests pass, Accountability Gate passes, Review Card recommends `APPROVE`. Merging deploys to staging and records a verified row on the Pages Accountability Ledger.

### Scenario B: Unvetted AI Code (Gate & Secret Catch)
1. Push branch: `git push -u origin demo/scenario-b-bad-gate`.
2. Open MR with description: `Adds admin tool without linked issue.`
3. **Result**:
   - `accountability-gate` fails the pipeline due to a missing `Assisted-by:` trailer.
   - GitLab Secret Detection flags the dummy AWS key (`AKIAIOSFODNN7EXAMPLE`).
   - Accountability Card highlights scope creep (`unrelated_admin_tool.py`), rates risk as **HIGH**, and recommends **REJECT**.

### Scenario C: Post-Deploy Incident & Root Cause Trace
1. Push branch: `git push -u origin demo/scenario-c-bad-healthcheck` and merge to `main`.
2. Staging deploy runs, but `staging-healthcheck` fails on `GET /health` (`HTTP 500`).
3. Open an issue using `.gitlab/issue_templates/incident.md`.
4. Mention `@incident-trace`: Flow 3 isolates the culprit commit, traces it back to the original MR and prompt provenance, and outputs:
   ```bash
   git revert <culprit_sha> --no-edit && git push origin main
   ```
5. Execute the revert command to restore staging health immediately.

---

## 📄 License

This project is licensed under the [MIT License](LICENSE) &copy; 2026 &lt;YOUR NAME&gt;.

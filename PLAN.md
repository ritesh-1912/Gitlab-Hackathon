# Implementation Plan: DuoGate (AI Accountability Pipeline)

**Hackathon**: GitLab Transcend Hackathon — "Life After Code" (Devpost)  
**Theme**: Post-Code Generation DevSecOps Lifecycle Automation via GitLab Duo Agent Platform  
**Target Duration**: 7.5 hours (including 1-hour buffer)  
**Hard Submission Deadline**: Oct 27, 2026, 6:30 pm IST (1:00 pm UTC)  
**Strict Project Schedule**:
- **Code Freeze**: 3:30 pm IST (Oct 27)
- **Demo Verification & Walkthrough**: 3:30 pm – 5:00 pm IST (Oct 27)
- **Devpost Submission**: 5:30 pm IST (Oct 27) — *1-hour safety buffer before the 6:30 pm IST hard deadline*

---

## 1. Core Concept & Honest Limitation

- **Problem**: Engineering teams ship AI-generated and AI-assisted code faster than they can verify, trace, or govern it. When production incidents occur, tracing back to the origin prompt, developer intent, and responsible agent is virtually impossible.
- **Solution**: An end-to-end DevSecOps pipeline coupled with GitLab Duo Custom Flows that enforces commit provenance trailers (`Assisted-by:`) and issue intent linking (`Closes #<id>`), gates merges via CI, generates a static "Accountability & Provenance Ledger" via GitLab Pages (derived reliably from repository commit history), and uses Duo custom flows for pre-merge intent verification and post-incident root-cause trace.
- **Architecture Clarification**: GitLab Pages hosts the static Accountability Ledger; it does not host or deploy the Python/Flask service. The `healthcheck` CI stage is strictly an in-process smoke test simulating staging verification before promotion, not live production monitoring.
- **Honest Limitation Stated in Docs**: AI origin cannot be reliably detected retrospectively in legacy commits without metadata. The system establishes and enforces strict provenance and intent contracts *going forward*.

---

## 2. Resource & Credit Budget

- **Duo Credit Allocation**: 500 total compute credits.
- **Maximum Execution Ceiling**: Up to **12 flow runs maximum** (this is an upper ceiling to conserve credits, not a quota):
  1. *Run 1*: Tracer bullet validation on test issue.
  2. *Runs 2–3 (Optional)*: Flow 1 (Intent) prompt validation.
  3. *Runs 4–6 (Optional)*: Flow 2 (Accountability Card) MR review iterations.
  4. *Runs 7–8 (Optional)*: Flow 3 (Incident Trace) validation on incident issue.
  5. *Runs 9–12 (As needed)*: Final demo walkthrough execution.

---

## 3. Final Repository File Tree

```
DuoGate/
├── .gitlab-ci.yml                 # Stages: test -> security -> gate -> deploy -> healthcheck
├── LICENSE                        # MIT License
├── README.md                      # Architecture, setup steps, lifecycle mapping, limitations
├── docs/                          # Official GitLab reference docs
│   └── README.md                  # Index of official URLs and Flow Registry v1 ambient rules
├── flows/                         # GitLab Duo Custom Flows (Registry v1 ambient schema)
│   ├── tracer-bullet.yml          # Minimal 15-line flow to verify mention trigger & issue note
│   ├── intent-flow.yml            # Flow 1: Intent & Acceptance Criteria (Issue mention)
│   ├── accountability-card.yml    # Flow 2: Origin, Diff, Scope Creep & Risk Assessment (MR mention)
│   └── incident-trace.yml         # Flow 3: Post-Deploy Incident Root Cause & Provenance (Incident mention)
├── scripts/
│   ├── accountability_gate.py     # CI gate: validates git log trailers & CI_MERGE_REQUEST_DESCRIPTION
│   ├── build_ledger.py            # Aggregates deployment history into static HTML for GitLab Pages
│   ├── smoke_test.py              # In-process smoke test runner for staging healthcheck
│   └── seed_demo.sh               # Automation script to seed Demo Scenarios A, B, and C
├── src/
│   ├── app.py                     # Minimal Inventory Service (<100 lines Python/Flask)
│   └── requirements.txt           # Minimal dependencies (Flask, pytest, requests)
└── tests/
    └── test_app.py                # Unit tests for inventory endpoints & healthcheck
```

> **Artifacts Note**: `public/` (for GitLab Pages) is created dynamically during CI by `build_ledger.py` and published as a pipeline artifact; it is not committed to the repository.

---

## 4. Flow Architecture & Toolset Rules (Verified against GitLab Docs)

### A. Strict Schema Adherence (v1 Ambient)
*   **Allowed Top-Level Keys**: `version: "v1"`, `environment: ambient`, `components: [...]`, `prompts: [...]`, `routers: [...]`, `flow: { entry_point: ... }`, and optional `coding_environment: none | full`.
*   **FORBIDDEN / RESTRICTED KEYS**:
    *   Do **NOT** include `name`, `description`, or `product_group` at root.
    *   Do **NOT** use `model`, `stop`, or `response_schema_id` inside prompts/components.
*   **Component Structure**:
    *   `type: AgentComponent`
    *   `prompt_id: "<id>"`
    *   `inputs`: `[{from: "context:goal", as: "user_goal"}, {from: "context:project_id", as: "project_id"}]`
    *   `toolset`: List of confirmed tools.
    *   `ui_log_events`: `["on_agent_final_answer", "on_tool_execution_success", "on_tool_execution_failed"]`
*   **Prompt Structure**:
    *   `name`, `prompt_id`, `unit_primitives: []`, `prompt_template: { system: "...", user: "...", placeholder: history }`, `params: { timeout: 300 }`.
*   **Routers & Flow**:
    *   `routers: [{from: "<component>", to: "end"}]`
    *   `flow: { entry_point: "<component>" }`

### B. Toolset Matrix & Fallback Strategies

| Tool Name | Status | Verified Function | Fallback if Unavailable |
| :--- | :--- | :--- | :--- |
| `get_issue` | **CONFIRMED** | Fetch issue title, description, and metadata via `project_id` & `issue_iid`. | Rely on goal payload text (`Input: ...`). |
| `create_issue_note` | **CONFIRMED** | Post structured markdown comment to issue. | Core output mechanism for all flows. |
| `get_repository_file` | **CONFIRMED** | Read file content from repo at specific ref/path. | Read fallback files or inspect commit history. |
| `list_repository_tree` | **CONFIRMED** | List directories and files in repository. | Target known fixed file paths in `src/` and `scripts/`. |
| `find_files` | **CONFIRMED** | Search for files by pattern. | `list_repository_tree`. |
| `blob_search` | **CONFIRMED** | Search file contents across repository. | Direct file inspection via `get_repository_file`. |
| `create_file` | **CONFIRMED** | Create a new file in repository. | N/A (Flows primarily post analytical comments). |
| `create_commit` | **CONFIRMED** | Commit staged changes to repository. | N/A (Flows output git commands for human execution). |
| `create_merge_request` | **CONFIRMED** | Open new merge request. | Provide `git revert` command in issue comment. |
| `get_merge_request` | **VERIFY** | Read MR details, diff, or description. | Parse MR URL/IID from goal; read gate artifact `gate_report.json` via repo/issue link. |
| `create_merge_request_note`| **VERIFY** | Post comment directly on MR. | Post report comment to the linked issue note (`create_issue_note`). |
| `get_pipeline_job_log` | **VERIFY** | Retrieve log of failed CI job. | Post triage guidance based on smoke test error patterns and `gate_report.json`. |

### C. Trigger Conventions
*   **Primary Trigger for All Flows**: `mention` (`@<flow-service-account>`).
    *   Goal format:
        ```text
        Input: <comment text>
        Context: {Issue IID: N}
        ```
*   **Secondary Trigger (Assign / Reviewer)**: Prompts must parse both integer IIDs and typed URLs:
    ```text
    Context:
    MergeRequest: https://gitlab.example.com/.../merge_requests/10
    ```
*   **Pipeline Event Trigger**: Controlled by feature flag (`ai_flow_trigger_pipeline_event`); marked as a **stretch goal** only.

---

## 5. Ordered Task List & Time Budget (7h 30m Total)

| Task ID | Phase / Deliverable | Scope & Actions | Time Estimate | Target Completion (IST) |
| :--- | :--- | :--- | :--- | :--- |
| **T0** | **Setup & Official Docs Reference** | Verified `/docs/` with all official specifications and authoring rules. | 30 min | 6:30 pm (Day 1) |
| **T1** | **Host Target App & Unit Tests** | Build `<100` line Flask inventory app (`src/app.py`), requirements, and pytest suite (`tests/test_app.py`). | 30 min | 7:00 pm (Day 1) |
| **T2** | **Accountability Gate & Ledger Scripts** | Author `accountability_gate.py` (checks `Assisted-by` & `Closes #<id>`, outputs `gate_report.json`), `build_ledger.py`, and `smoke_test.py`. | 45 min | 7:45 pm (Day 1) |
| **T3** | **GitLab CI/CD Pipeline Configuration** | Configure `.gitlab-ci.yml` (test -> security -> gate -> deploy -> healthcheck) with `workflow:rules`. | 45 min | 8:30 pm (Day 1) |
| **T4** | **Tracer Bullet Flow & Validation** | Author 15-line `flows/tracer-bullet.yml`. Validate single comment output on mention trigger in GitLab. | 30 min | 9:00 pm (Day 1) |
| **T5** | **Duo Custom Flows (Flows 1, 2, 3)** | Author `flows/intent-flow.yml`, `flows/accountability-card.yml`, and `flows/incident-trace.yml`. | 60 min | 10:00 pm (Day 1) |
| **T6** | **GitLab UI Setup & Repo Push** | Create project, set merge commit strategy, configure Pages, register flows in UI, push to `main`. | 45 min | 10:45 pm (Day 1) |
| **T7** | **Demo Scenarios Execution** | Seed & run Scenario A (clean pass), Scenario B (gate & secret caught), Scenario C (broken healthcheck + trace + built-in Fix flow). | 60 min | 11:45 pm (Day 1) |
| **T8** | **Documentation, License & Devpost** | Author `README.md`, `LICENSE`, `DEMO.md`, and `DEVPOST.md`. | 45 min | 12:30 am (Day 2) |
| **T9** | **Buffer / Review Sleep Window** | Verification buffer before final walkthrough. | 60 min | — |
| **T10** | **Demo Walkthrough & Submission** | Execute walkthrough scenarios, verify pipeline, and submit prior to 5:30 pm IST deadline. | 90 min | **5:00 pm (Day 2)** |

---

## 6. Scope Management: MUST / SHOULD / CUT-IF-LATE

### MUST (Core MVP — Non-Negotiable)
*   **Host Target App**: Minimal Flask inventory service (`src/app.py`) `<100` lines + 2-3 passing unit tests.
*   **Accountability Gate**: `scripts/accountability_gate.py` checking commits introduced by MR (`origin/main..HEAD` with fallback) and MR description (with fallback), parsing `gl-secret-detection-report.json`, writing `gate_report.json`.
*   **CI Pipeline**: `.gitlab-ci.yml` running `test` -> `security` (Secret Detection) -> `gate` -> `deploy` (Pages) -> `healthcheck` (in-process smoke test).
*   **Accountability Ledger**: `scripts/build_ledger.py` generating static HTML published via GitLab Pages to environment `staging` (Pages serves the static ledger; the Flask app is verified via in-process smoke test, not hosted on Pages). The ledger derives persistent history from git commit log.
*   **Tracer Bullet Flow**: `flows/tracer-bullet.yml` successfully posting an issue comment on mention.
*   **Flow 2 ("Accountability Card")**: GitLab Duo custom flow evaluating provenance, intent, risk, and human recommendation (using confirmed tools `get_issue`, `get_repository_file`, `create_issue_note` with MR diff as optional).
*   **Demo Scenario A**: Clean MR showing end-to-end passage into the Accountability Ledger.
*   **Compliance & Metadata**: Root `LICENSE` (MIT), setup `README.md`, public GitLab repo, Devpost text description.

### SHOULD (High-Impact Differentiators)
*   **Flow 1 ("Intent")**: GitLab Duo flow triggered on Issue mention to draft acceptance criteria, task checklist, and out-of-scope boundaries.
*   **Flow 3 ("Incident Trace")**: GitLab Duo flow triggered on incident issue mention to trace failed healthcheck back to responsible commit/MR and output `git revert`.
*   **GitLab Built-in "Fix CI/CD Pipeline" Flow**: Demonstrate GitLab's native agent repairing the pipeline after Flow 3 identifies the root cause.
*   **Demo Scenario B**: Bad MR showing gate catching missing trailer and Secret Detection catching dummy test secret.
*   **Demo Scenario C**: Broken healthcheck demonstrating automated staging incident and rollback suggestion.
*   **GitLab SAST Integration**: Inclusion of GitLab official SAST template.

### CUT-IF-LATE (Drop Immediately if Behind Schedule)
*   *Flow 3 pipeline-event trigger*: Drop feature-flagged pipeline trigger; rely exclusively on comment mention (`@<flow> trace`).
*   *Live execution of Scenario B & C*: Use pre-executed pipeline history and show diffs/logs directly.
*   *Ledger CSS styling*: Keep plain HTML table with minimal inline styles.

---

## 7. Risks, VERIFY Items & Fallbacks

| Item / Feature | Risk / Uncertainty | VERIFY Step | DevSecOps Fallback Strategy |
| :--- | :--- | :--- | :--- |
| **Flow Tool Availability** | Tools like `create_merge_request_note` or `get_pipeline_job_log` are unconfirmed in runtime. | **VERIFY**: Test in Tracer Bullet and Flow 1. | Use only confirmed tools: `create_issue_note` and `get_issue`. Flow 2 posts the card to the linked issue if MR note fails; Flow 3 posts the revert command to the incident issue. |
| **Trigger Payload Nuances** | Reviewer/Assign events may pass URLs instead of IIDs depending on feature flags. | **VERIFY**: Check goal format in test trigger. | System prompt explicitly instructs the agent to extract numbers via regex whether format is `{Issue IID: 1}` or `.../merge_requests/1`. |
| **MR Environment Variables in CI** | `CI_MERGE_REQUEST_DESCRIPTION` is only present in merge request pipelines. | **VERIFY**: Test with `workflow:rules`. | `accountability_gate.py` falls back to reading commit message bodies or CLI parameter if variable is empty. |
| **Credit Consumption** | Each flow run consumes credits against the 500 budget. | **VERIFY**: Monitor credit usage in GitLab Duo usage dashboard. | Hard limit of 12 runs total; execute Tracer Bullet first to catch YAML issues before consuming credits on Flows 1–3. |
| **Secret Detection Default Mode** | GitLab Secret Detection does not fail jobs by default. | **VERIFY**: Check job exit code on fake secret. | `accountability_gate.py` parses `gl-secret-detection-report.json` and fails the gate if secrets are detected. |

---

## 8. Sequential Build Prompts (Module by Module)

### Prompt 1: Scaffold Target App & Unit Tests
```text
PROMPT 1: Build the Target Application & Test Suite.
Context: Create a tiny Python 3 / Flask inventory microservice (<100 lines) and pytest suite.
Files to create:
1. src/app.py: Flask app with endpoints GET /, GET /items, POST /items, GET /health.
2. src/requirements.txt: flask>=3.0.0, pytest>=8.0.0.
3. tests/test_app.py: Pytest testing /health, GET /items, and POST /items.
Make sure all tests pass locally. Keep code minimal, clean, and without external database dependencies.
```

### Prompt 2: Accountability Gate Script
```text
PROMPT 2: Build the Accountability Gate Script.
Context: Create scripts/accountability_gate.py.
Requirements:
1. Run in CI merge request pipelines without any external GitLab API tokens.
2. Inspect commits introduced by the MR (e.g., git log origin/main..HEAD, or merge base; fall back gracefully to HEAD commit if shallow or detached).
3. Check each introduced commit for the trailer: "Assisted-by: <tool|agent|none>".
4. Inspect CI_MERGE_REQUEST_DESCRIPTION for intent link: "Closes #<id>" or "Fixes #<id>". If variable is empty/missing, fall back to checking commit message bodies or CLI --description flag.
5. Inspect gl-secret-detection-report.json if present: parse findings and fail the gate if vulnerabilities exist (do not assume the security job failed).
6. If missing trailer, missing intent link, or secrets detected, fail with exit code 1.
7. Write structured JSON artifact to gate_report.json containing status, trailers, linked issue, secret findings, and violations.
8. Support local test execution via CLI arguments.
```

### Prompt 3: Ledger Generator & Smoke Test Runner
```text
PROMPT 3: Build the Accountability Ledger Generator & Smoke Test Script.
Files to create:
1. scripts/build_ledger.py: Reads gate_report.json, queries git commit history (hash, author, date, Assisted-by trailers) to produce a persistent, accurate git-log-backed Accountability & Provenance Ledger in public/index.html. Note: GitLab Pages serves this static ledger; the Flask inventory app is not hosted on Pages.
2. scripts/smoke_test.py: In-process HTTP client test against app.py's /health endpoint to run as a CI smoke test stage (not production monitoring). Supports a flag --fail-on-purpose to simulate an unhealthy staging release.
```

### Prompt 4: GitLab CI/CD Pipeline Configuration
```text
PROMPT 4: Configure .gitlab-ci.yml.
Context: End-to-end DevSecOps pipeline covering test, security, gate, deploy, healthcheck.
Stages:
- test: Runs pytest src/ tests/.
- security: Includes GitLab SAST and Secret-Detection templates (artifacts archived).
- gate: Runs scripts/accountability_gate.py, parses Secret Detection report, outputs gate_report.json artifact.
- deploy: (main branch only) Runs scripts/build_ledger.py to populate public/, defines environment: staging, publishes static ledger to GitLab Pages.
- healthcheck: Runs scripts/smoke_test.py as an in-process staging smoke test against the service.
Ensure proper workflow:rules so merge request pipelines properly populate CI_MERGE_REQUEST_* variables.
```

### Prompt 5: GitLab Duo Tracer Bullet Flow
```text
PROMPT 5: Author Duo Tracer Bullet Flow.
Context: Create flows/tracer-bullet.yml (minimal ~15 lines) adhering strictly to Flow Registry v1 ambient schema.
Requirements:
1. Top-level keys: version: "v1", environment: ambient, coding_environment: none, components, prompts, routers, flow.
2. Component uses AgentComponent with toolset: ["create_issue_note"].
3. Trigger: Mention on an Issue.
4. Behavior: Parse issue IID from context:goal and post a simple confirmation note: "🚀 Tracer Bullet: Duo Agent flow trigger and issue note verified."
5. Must run cleanly to validate flow registration and credit expenditure before proceeding to Flows 1-3.
```

### Prompt 6: GitLab Duo Custom Flow 1 — Intent
```text
PROMPT 6: Author Duo Custom Flow 1 (Intent Definition).
Context: Custom flow in flows/intent-flow.yml based on GitLab Flow Registry v1 ambient specification.
Trigger: Mention on an Issue (@<flow>).
Inputs: context:goal and context:project_id.
Toolset: ["get_issue", "create_issue_note"].
Behavior:
- Extract Issue IID from goal.
- Fetch issue details with get_issue.
- Generate structured acceptance criteria, a checklist, and an explicit "Out of Scope" list.
- Post this as a structured comment via create_issue_note to establish human intent before coding starts.
```

### Prompt 7: GitLab Duo Custom Flow 2 — Accountability Card
```text
PROMPT 7: Author Duo Custom Flow 2 (Accountability Card).
Context: Custom flow in flows/accountability-card.yml based on Flow Registry v1 ambient specification.
Trigger: Mention on an MR or Issue (@<flow>).
Toolset: ["get_issue", "get_repository_file", "create_issue_note"]. (Note: MR diff / MR note tools are treated as optional capabilities; baseline and fallback rely exclusively on confirmed tools).
Behavior:
- Parse resource context (handle both IID and resource URL).
- Inspect gate_report.json and source files via confirmed tools.
- Synthesize an Accountability Card:
  1. Origin: Provenance trailers (Assisted-by: ...).
  2. Intent Match: Acceptance criteria verified vs unfulfilled.
  3. Scope Creep: Changes detected outside the original issue intent.
  4. Risk Assessment: LOW / MEDIUM / HIGH with justification.
  5. Recommendation: APPROVE / REJECT / REVISE (human makes final call).
- Post card via create_issue_note.
```

### Prompt 8: GitLab Duo Custom Flow 3 — Incident Trace
```text
PROMPT 8: Author Duo Custom Flow 3 (Incident Trace).
Context: Custom flow in flows/incident-trace.yml.
Trigger: Mention on an Incident Issue (@<flow> trace).
Toolset: ["get_issue", "get_repository_file", "list_repository_tree", "create_issue_note"]. (Note: Pipeline job log tools are optional; fallback relies on confirmed tools and smoke test logs).
Behavior:
- Parse incident context.
- Inspect latest deployment commit and gate report.
- Trace back to the originating MR, linked issue, and AI prompt/tool provenance trailer.
- Output root cause analysis and the exact command: `git revert <commit_sha>` for instant remediation.
```

### Prompt 9: Demo Seeding Automation & Runbooks
```text
PROMPT 9: Create Demo Scenarios & Seeding Automation.
Files to create:
1. scripts/seed_demo.sh: Shell script that automates setting up git branches and commit trailers for:
   - Scenario A (Clean MR): Clean feature commit with proper trailer and issue link.
   - Scenario B (Bad MR): Scope creep code, missing trailer, and a fake dummy secret (e.g., FAKE_DEMO_AWS_KEY="AKIAZ7QX3PLM9RTK2VNB").
   - Scenario C (Incident): Commit that breaks /health logic, triggering healthcheck failure, followed by Flow 3 trace and GitLab's built-in "Fix CI/CD Pipeline" flow.
2. DEMO.md: Plain step-by-step runbook for Scenarios A, B, and C.
```

### Prompt 10: Documentation, Licensing & Devpost Submission Pack
```text
PROMPT 10: Complete Repository Documentation & Devpost Submission Pack.
Files to create:
1. LICENSE: Standard MIT License.
2. README.md: Architecture diagram, lifecycle stages covered, setup instructions, honest limitation disclaimer (cannot detect AI origin in legacy commits without provenance trailers), and instructions for running the flows.
3. DEVPOST.md: Devpost summary, inspiration, what it does, how we built it, challenges, accomplishments, and what's next.
```

---

## 9. Manual Steps to Execute in GitLab Web UI

1. **Create Project**:
   * Create a new **Public** project named `DuoGate`.
   * Verify GitLab Duo Enterprise / Ultimate features are active on the namespace.
2. **Configure Merge Settings**:
   * Navigate to **Settings > Merge requests**.
   * Under **Merge method**, select **Merge commit** (ensures individual commit history and `Assisted-by:` trailers are preserved in `main`).
   * Save changes.
3. **Configure GitLab Pages**:
   * Navigate to **Deploy > Pages**.
   * Ensure Pages access is set to **Everyone** (publicly viewable ledger).
4. **Register GitLab Duo Custom Flows**:
   * Navigate to **Settings > GitLab Duo > Flows** (or **Duo Studio**).
   * Register Tracer Bullet: Paste `flows/tracer-bullet.yml`, enable `mention` trigger.
   * Register Flow 1: Paste `flows/intent-flow.yml`, enable `mention` trigger.
   * Register Flow 2: Paste `flows/accountability-card.yml`, enable `mention` trigger.
   * Register Flow 3: Paste `flows/incident-trace.yml`, enable `mention` trigger.
5. **Push Codebase**:
   * Set remote: `git remote add gitlab https://gitlab.com/gitlab-ai-hackathon/transcend-october-2026/43738285/showcase`.
   * Push initial branch to GitLab: `git push -u gitlab main`.
6. **Verify Initial Pipeline & Tracer**:
   * Confirm the pipeline on `main` passes and deploys the initial Accountability Ledger.
   * Test Tracer Bullet on an issue with `@<flow>` to verify credit expenditure and response.

---

## 10. DevSecOps Lifecycle Stages Mapping

```
[PLAN]       Flow 1: Issue triage, acceptance criteria, checklist, scope boundary
   │
[CREATE]     Feature development with mandatory `Assisted-by:` trailers & `Closes #` links
   │
[VERIFY]     Pytest unit tests, `accountability-gate` CI check, Flow 2 MR Review Card
   │
[SECURE]     GitLab SAST & Secret Detection scanning in merge request pipeline
   │
[RELEASE]    GitLab CI Deploy job (main branch) registering `staging` environment
   │
[GOVERN]     Public Accountability Ledger published to GitLab Pages tracking provenance
   │
[MONITOR]    Post-deploy in-process healthcheck & smoke test suite
   │
[REMEDIATE]  Flow 3: Incident Trace isolating prompt origin & outputting `git revert`
   │         + GitLab Built-in "Fix CI/CD Pipeline" Flow repairing the staging build
```

---

*This plan is verified against official GitLab Duo v1 documentation, adheres to strict credit/run budgets, and meets the Oct 27, 2026 hackathon deadline.*

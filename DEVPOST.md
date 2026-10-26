# Devpost Submission: <PROJECT_NAME>

**Event**: GitLab Transcend Hackathon — "Life After Code"  
**Track**: Path A (Fresh Project) & Supervised Autonomy  
**Repository**: [<GITLAB_PROJECT_URL>](<GITLAB_PROJECT_URL>)  
**Accountability Ledger**: [<PAGES_URL>](<PAGES_URL>)

---

## 💡 Inspiration

Generative AI has fundamentally solved code authoring. Code generation assistants can write microservices, functions, and unit tests in seconds. But as teams ship AI-assisted code at unprecedented velocity, software engineering faces a new, dangerous bottleneck: **the governance and accountability vacuum**.

Most organizations today cannot answer simple questions about changes deployed to production:
- *Where did this change come from? (A human, a Duo chat prompt, or an autonomous background agent?)*
- *What specific requirement was it authorized to fulfill?*
- *When an outage occurs at 2:00 AM, how do we trace the failure back to the responsible commit, developer intent, and MR?*

We built **`<PROJECT_NAME>`** to prove that **"Life After Code"** must be about **governance, provenance, and rapid incident triage**. By combining automated CI pipeline gates with the GitLab Duo Agent Platform, we turn unvetted AI code generation into a transparent, verifiable DevSecOps lifecycle.

---

## 🛠️ What It Does

`<PROJECT_NAME>` is an end-to-end DevSecOps system composed of an automated CI accountability gate, a continuous static Accountability Ledger hosted on GitLab Pages, and three custom GitLab Duo flows that supervise changes from issue definition to post-incident remediation:

1. **Mandatory Provenance Contracts**:
   - Every commit must include an RFC-compliant Git trailer: `Assisted-by: <tool|agent>` or `Assisted-by: none`.
   - Every Merge Request must link to a verified issue intent: `Closes #<id>` or `Fixes #<id>`.
2. **Automated CI Accountability Gate (`scripts/accountability_gate.py`)**:
   - Inspects exclusively commits introduced by the MR (`base..head`), explicitly excluding merge commits.
   - Enforces valid `Assisted-by:` trailers and issue intent linkage.
   - Ingests GitLab Secret Detection reports (`gl-secret-detection-report.json`) and halts merges on exposed credentials.
   - Supports a default-branch push mode that evaluates `CI_COMMIT_BEFORE_SHA..CI_COMMIT_SHA` (or `HEAD` if initial push).
   - Generates a structured `gate_report.json` artifact and fails non-compliant builds.
3. **Continuous Accountability Ledger on GitLab Pages (`scripts/build_ledger.py`)**:
   - Reconstructs the complete provenance audit trail directly from Git commit history.
   - Calculates provenance compliance rates, AI vs. human commit ratios, and active gate status.
   - Published statically to GitLab Pages (`staging` environment) with zero external database dependencies.
4. **Three GitLab Duo Custom Flows**:
   - **Flow 1 ("Intent Definition")**: Triggered on mention on an issue (`@<intent-flow-handle>`). Generates acceptance criteria, task checklists, and an explicit **Out-of-Scope** guardrail list to prevent AI scope creep before coding starts.
   - **Flow 2 ("Accountability Card")**: Triggered on mention on an MR review (`@<card-flow-handle>`). Evaluates diffs, trailers, intent match, and scope creep. Emits an advisory review card rating risk as LOW/MEDIUM/HIGH with an explicit recommendation (APPROVE/REJECT).
   - **Flow 3 ("Incident Trace")**: Triggered on mention on an incident issue (`@<incident-flow-handle>`) after staging smoke test failures. Traces using the incident issue's fields (culprit SHA, MR, linked issue) and available tools, outputting the exact `git revert <sha>` command for instant remediation.

---

## 🤖 How We Built It & Used the GitLab Duo Agent Platform

We designed `<PROJECT_NAME>` from the ground up to utilize the official **GitLab Duo Agent Platform Flow Registry v1 specification**:

- **Strict Ambient Schema Compliance**:
  - Our custom flows (`flows/intent.yml`, `flows/accountability-card.yml`, `flows/incident-trace.yml`, `flows/tracer-bullet.yml`) strictly follow the Flow Registry v1 schema: `version: "v1"`, `environment: ambient`, top-level `components`, `prompts`, `routers`, and `flow: { entry_point: ... }`.
  - We strictly omitted restricted keys (`name`, `description`, `product_group` at top level; `model`, `stop` in prompts).
- **Verified Toolsets & Graceful Fallbacks**:
  - Rather than inventing unconfirmed tools, our flows operate on confirmed platform tools (`get_issue`, `get_repository_file`, `list_repository_tree`, `create_issue_note`).
  - For MR reviews, our Accountability Card parses the linked issue from the mention context, audits repository files and gate artifacts, and posts structured notes without relying on unconfirmed diff APIs.
- **Mention Triggers & Dual-Format Parsing**:
  - Configured `@mention` triggers on Issues and Merge Requests (`@<intent-flow-handle>`, `@<card-flow-handle>`, `@<incident-flow-handle>`).
  - Prompts parse both integer IIDs (`Context: {Issue IID: 1}`) and typed URLs (`MergeRequest: https://.../10`).
- **Supervised Autonomy by Design**:
  - The flows do not autonomously push code or create unauthorized MRs. Every output ends with the explicit mandate: **"Advisory only: a human decides."**

---

## 🔄 DevSecOps Lifecycle Stages Covered

`<PROJECT_NAME>` covers 7 of GitLab's 9 lifecycle stages (plan, create, verify, secure, release, monitor, govern) plus incident remediation:

```
[PLAN]       Flow 1 (Intent Definition) establishes acceptance criteria & out-of-scope boundaries
   │
[CREATE]     Developer / Duo creates code with mandatory `Assisted-by:` trailers & `Closes #` links
   │
[VERIFY]     Pytest suite + Flow 2 (Accountability Card) assessing diff intent match & scope creep
   │
[SECURE]     GitLab SAST & Secret Detection scanning in MR pipeline + gate ingestion
   │
[RELEASE]    GitLab CI deploy job registering environment `staging` on default branch
   │
[GOVERN]     Accountability Gate enforcement + continuous Accountability Ledger on GitLab Pages
   │
[MONITOR]    In-process staging healthcheck smoke test runner (`scripts/smoke_test.py`)
   │
[REMEDIATE]  Flow 3 (Incident Trace) isolating culprit commit & outputting instant `git revert`
```

---

## 🚧 Challenges We Encountered

1. **Flow Registry v1 Schema Restrictions**: Early in design, custom flow schema validation rejected standard YAML keys like `name` and `model`. By studying the raw v1 registry specifications and official examples, we adapted all custom flows to use `environment: ambient`, `AgentComponent`, and proper prompt parameter structures.
2. **Git Clone Depth in GitLab CI**: GitLab CI defaults to shallow clones (`GIT_DEPTH: 20` or `50`), which breaks `git rev-list base..head` if the branch diverged further back. Setting `GIT_DEPTH: "0"` in `.gitlab-ci.yml` ensured reliable provenance inspection across all MRs.
3. **Preventing False Passes in Governance**: It was critical that missing or malformed security reports or gate artifacts never showed a false pass. We implemented fail-closed logic across both `accountability_gate.py` and `build_ledger.py`.
4. **Honest Stated Limitation**: AI generation origin cannot be reliably detected retrospectively in legacy Git commits. We solved this by clearly documenting this constraint and establishing an enforceable, forward-looking provenance contract.

---

## 🏆 Accomplishments That We're Proud Of

- **49 Automated Tests with 100% Determinism**: Complete coverage across unit endpoints, Git trailer extraction, MR intent parsing, push mode all-zeros base handling, and XSS escaping.
- **Completely Self-Contained Architecture**: Zero external databases, zero third-party SaaS services, and zero external hosting. Everything runs in GitLab CI, GitLab Pages, and the Duo Agent Platform.
- **3 Deterministic Demo Scenarios**: Automated with `./scripts/seed_demo.sh` to demonstrate clean passage (Scenario A), automated gate & secret rejection with fake key `AKIAZ7QX3PLM9RTK2VNB` (Scenario B), and post-deployment incident root-cause triage (Scenario C). Demo branches are pushed to GitLab only.

---

## 🔮 What's Next for <PROJECT_NAME>

1. **Cryptographic Agent Attestation**: Integrating Sigstore / Cosign to cryptographically sign commits with Duo Agent identities alongside metadata `Assisted-by:` trailers.
2. **Automated Pipeline Event Triggers**: Upgrading Flow 3 from comment mention to native `pipeline_failed` event triggers once the feature flag is generally available.
3. **Semantic Drift Detection**: Using Duo embeddings to measure semantic drift between the initial prompt tokens and the merged diff over time.

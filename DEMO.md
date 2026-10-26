# 🎬 3-Minute Hackathon Demo Walkthrough: <PROJECT_NAME>

**Theme**: Life After Code — Autonomous DevSecOps Governance with GitLab Duo Agent Platform  
**Target Duration**: 2 minutes 50 seconds (< 180 seconds)  
**Submission**: GitLab Transcend Hackathon (Devpost)

---

## ⏱️ Timeline Overview

| Timestamp | Lifecycle Stage | Screen Action | Focus |
| :--- | :--- | :--- | :--- |
| **0:00 – 0:25** | **Problem & Concept** | Title slide / Repo README | Generative AI solved code generation; governance & triage are the real bottleneck. |
| **0:25 – 1:15** | **Plan & Release** | Issue #1 -> MR #1 -> Pages | Flow 1 (Intent), Clean MR, Gate pass, Flow 2 (Review Card), Ledger deploy. |
| **1:15 – 1:55** | **Secure & Govern** | MR #2 (Bad change) | Gate catches missing trailer, Secret Detection catches fake key, Review Card rejects. |
| **1:55 – 2:40** | **Monitor & Remediate** | Incident Issue -> Flow 3 | Broken staging healthcheck, Flow 3 traces culprit & provenance, outputs `git revert`. |
| **2:40 – 3:00** | **Conclusion** | GitLab Pages Ledger | Full lifecycle audit trail; Supervised Autonomy ("A human decides"). |

---

## 🎬 Minute-by-Minute Script & Walkthrough

### Part 1: The Problem (0:00 – 0:25)
**Screen Setup**: Show repository root or architecture diagram in `README.md`.

* **Spoken Narrative**:
  > *"Generative AI solved code authoring, but it created an operational crisis: teams are shipping AI-assisted code faster than they can verify intent or trace provenance. When something breaks in production, who wrote it, what was it meant to do, and which agent assisted it?*
  > 
  > *Welcome to `<PROJECT_NAME>`—the AI Accountability Pipeline built on the GitLab Duo Agent Platform. We enforce provenance contracts at commit time, gate merges through CI, maintain a live Accountability Ledger on GitLab Pages, and use Duo Custom Flows to review intent and trace incidents."*

---

### Part 2: Plan, Verify & Release — Scenario A (0:25 – 1:15)
**Screen Setup**: Open GitLab UI on **Issue #1: "Add Inventory Summary Endpoint"**.

1. **Trigger Flow 1 (Intent)**:
   * **Action**: On Issue #1, post comment:
     ```text
     @intent-agent please define the acceptance criteria and scope boundaries.
     ```
   * **Spoken Narrative**:
     > *"We begin in the Plan stage. Before any code is generated, our Intent Flow analyzes the issue and posts verifiable acceptance criteria, a checklist, and explicit Out-of-Scope guardrails to stop AI scope creep."*

2. **Push Scenario A & Open MR**:
   * **Terminal Command**:
     ```bash
     git push -u origin demo/scenario-a-clean
     ```
   * **GitLab Action**: Open Merge Request with title `feat: add inventory summary endpoint` and description:
     ```text
     Implements aggregated inventory calculations. Closes #1
     ```
   * **Pipeline Run**: Point out `accountability-gate` running alongside `pytest` and `secret_detection`.

3. **Trigger Flow 2 (Accountability Card)**:
   * **Action**: In the MR comment thread, post:
     ```text
     @accountability-card please review this MR against issue #1.
     ```
   * **Spoken Narrative**:
     > *"In the MR pipeline, our gate confirms the `Assisted-by: gitlab-duo` trailer and `Closes #1` link. Our Accountability Card flow inspects the diff against the issue criteria, verifies zero scope creep, rates the risk as LOW, and recommends APPROVE. The human reviewer approves and merges."*

4. **Show GitLab Pages Ledger**:
   * **Action**: Click the `staging` environment link to show the **Accountability Ledger** on GitLab Pages (`public/index.html`).
   * **Spoken Narrative**:
     > *"On merge, the pipeline deploys to staging and records an immutable provenance row in our Accountability Ledger on GitLab Pages."*

---

### Part 3: Secure & Govern — Scenario B (1:15 – 1:55)
**Screen Setup**: Open terminal, push Scenario B.

1. **Push Bad Code**:
   * **Terminal Command**:
     ```bash
     git push -u origin demo/scenario-b-bad-gate
     ```
   * **GitLab Action**: Open MR titled `wip: add admin tool` with description:
     ```text
     Adds admin tool without linked issue.
     ```

2. **Inspect Pipeline Failure**:
   * **Action**: Open the running pipeline.
   * **Spoken Narrative**:
     > *"Now let's see what happens with unvetted AI code. This branch contains a missing provenance trailer, an unrelated file (`unrelated_admin_tool.py`), and a dummy test secret (`AKIAIOSFODNN7EXAMPLE`).*
     > 
     > *Notice the result: GitLab Secret Detection flags the credential, and our `accountability-gate` immediately fails the pipeline, blocking the merge. Even if triggered, our Accountability Card rates the risk as HIGH and explicitly recommends REJECT. The bad code never touches main."*

---

### Part 4: Monitor & Remediate — Scenario C (1:55 – 2:40)
**Screen Setup**: Show failed pipeline on default branch (`staging-healthcheck` failed).

1. **Simulate Incident & Open Incident Issue**:
   * **Action**: Show that a bad release failed the staging healthcheck smoke test (`HTTP 500 Database connection pool timeout`).
   * **Action**: Create a new issue using template **Incident**:
     - Pipeline URL: `https://gitlab.com/.../pipelines/101`
     - Culprit Commit SHA: `e485c19...`
     - MR Number: `!3`
     - Linked Issue Number: `1`

2. **Trigger Flow 3 (Incident Trace)**:
   * **Action**: In the incident issue comment, post:
     ```text
     @incident-trace please investigate root cause and prepare rollback command
     ```
   * **Spoken Narrative**:
     > *"In production, regressions happen. Here, a broken commit passed unit tests but failed our post-deploy healthcheck smoke test. We file an incident issue and trigger our Incident Trace flow.*
     > 
     > *The agent parses the telemetry, traces the regression to the exact commit, identifies its AI prompt origin, and provides the exact remediation command."*
   * **Action**: Copy the agent's output:
     ```bash
     git revert e485c19 --no-edit && git push origin main
     ```
   * **Action**: Paste in terminal or trigger GitLab's built-in **Fix CI/CD Pipeline** flow. The pipeline turns green.

---

### Part 5: Conclusion & Supervised Autonomy (2:40 – 3:00)
**Screen Setup**: Return to the **Accountability Ledger** on GitLab Pages.

* **Spoken Narrative**:
  > *"In under 3 minutes, we have demonstrated full DevSecOps lifecycle coverage: from planning intent and enforcing commit provenance, to automated security gating, staging deployment on Pages, and post-incident AI root-cause trace.*
  > 
  > *Most importantly, this embodies Supervised Autonomy: the agents perform the multi-step investigation, but as every card states, 'Advisory only: a human decides.' Thank you!"*

---

## 🛠️ Quick Pre-Flight Checklist Before Recording
- [ ] Run `./scripts/seed_demo.sh` to ensure all 3 local branches are prepared.
- [ ] Ensure GitLab project has Duo Agent Platform enabled.
- [ ] Ensure the 4 flow YAMLs are registered in **Automate > AI Agents & Flows**:
  - `tracer-bullet.yml` (tested first)
  - `intent.yml` (`@intent-agent`)
  - `accountability-card.yml` (`@accountability-card`)
  - `incident-trace.yml` (`@incident-trace`)
- [ ] Screen recording resolution set to 1080p, microphone audio clear, browser zoom at 110%.

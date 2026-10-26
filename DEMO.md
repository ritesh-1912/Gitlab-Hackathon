# Demo Runbook: <PROJECT_NAME>

This document provides a step-by-step runbook for demonstrating the three automated DevSecOps scenarios in `<PROJECT_NAME>`.

> [!NOTE]
> All demo branches are pushed to GitLab only. Ensure your local repository has the `gitlab` remote configured pointing to your GitLab project:
> ```bash
> git remote add gitlab <GITLAB_PROJECT_URL>
> ```

---

## Pre-Flight Setup

1. **Seed Local Branches**:
   Run the seeding script from the repository root:
   ```bash
   ./scripts/seed_demo.sh
   ```
   This generates the three demo branches locally (`demo/scenario-a-clean`, `demo/scenario-b-bad-gate`, and `demo/scenario-c-bad-healthcheck`) without pushing them.

2. **Register Custom Flows in GitLab**:
   In your GitLab project, open the project's Flows page (under the AI or Automate menu, depending on GitLab version), then New flow:
   - `flows/tracer-bullet.yml` (mention trigger: note handle `@<tracer-bullet-handle>`)
   - `flows/intent.yml` (mention trigger: note handle `@<intent-flow-handle>`)
   - `flows/accountability-card.yml` (mention trigger: note handle `@<card-flow-handle>`)
   - `flows/incident-trace.yml` (mention trigger: note handle `@<incident-flow-handle>`)

3. **Verify Staging Pages Configuration**:
   In **Deploy > Pages**, ensure Pages access is set to **Everyone** so the static Accountability Ledger can be viewed at `<PAGES_URL>`.

---

## Scenario A: Clean Feature MR (Passes & Deploys)

### 1. Plan Stage: Define Intent
1. In GitLab, create Issue #1 titled `Add Inventory Summary Endpoint`.
2. Post a comment mentioning `@<intent-flow-handle>`:
   ```text
   @<intent-flow-handle> please define the acceptance criteria and scope boundaries.
   ```
3. The Intent flow posts structured acceptance criteria, a checklist, and an explicit Out-of-Scope guardrail list.

### 2. Push Branch & Create Merge Request
1. Push the prepared clean branch to GitLab:
   ```bash
   git push -u gitlab demo/scenario-a-clean
   ```
2. Open a Merge Request on GitLab:
   - **Title**: `feat: add inventory summary endpoint`
   - **Description**: `Implements aggregated inventory summary calculation. Closes #1`
3. Observe the pipeline: `test`, `security` (Secret Detection), and `gate` (`accountability-gate`) run.

### 3. Review Stage: Accountability Card
1. In the MR comments, mention `@<card-flow-handle>`:
   ```text
   @<card-flow-handle> please review this MR against issue #1.
   ```
2. The agent evaluates the provenance trailer (`Assisted-by: gitlab-duo`), intent linkage (`Closes #1`), and diff.

### 4. Expected result (to be confirmed after the first run)
- `test` and `gate` jobs pass.
- Accountability Card rates risk as **LOW**, finds zero scope creep, and recommends **APPROVE**.
- Merge the MR into `main`.
- The `deploy` stage builds the static ledger via `scripts/build_ledger.py` and publishes to GitLab Pages (`<PAGES_URL>`).
- The `healthcheck` smoke test verifies the endpoint in-process and passes.
- Staging environment displays a compliant provenance entry in `public/index.html` (accessible at `<PAGES_URL>`).

---

## Scenario B: Unvetted AI Code (Gate & Secret Detection Catch)

### 1. Push Branch & Create Merge Request
1. Push the scenario B branch to GitLab:
   ```bash
   git push -u gitlab demo/scenario-b-bad-gate
   ```
   > [!NOTE]
   > This branch contains a missing `Assisted-by:` trailer, an unrelated file (`src/unrelated_admin_tool.py`), and a dummy test key (`AKIAZ7QX3PLM9RTK2VNB`, commented as FAKE strictly for Secret Detection demonstration). This key exists only on this branch and is never merged.
2. Open a Merge Request on GitLab:
   - **Title**: `wip: add admin tool`
   - **Description**: `Adds admin tool without linked issue.`

### 2. Review Stage: Pipeline Gate & Accountability Card
1. The MR pipeline runs automatically.
2. In the MR comments, mention `@<card-flow-handle>`:
   ```text
   @<card-flow-handle> please review this MR.
   ```

### 3. Expected result (to be confirmed after the first run)
- `accountability-gate` fails the CI pipeline due to missing provenance trailers.
- GitLab Secret Detection flags the dummy AWS credential (`AKIAZ7QX3PLM9RTK2VNB`).
- Accountability Card highlights scope creep (`unrelated_admin_tool.py`), rates risk as **HIGH**, and recommends **REJECT**.
- Merge is blocked, protecting `main` from unvetted code.

---

## Scenario C: Broken Release & Incident Remediation

### 1. Deploy Breaking Change
1. Push the scenario C branch to GitLab:
   ```bash
   git push -u gitlab demo/scenario-c-bad-healthcheck
   ```
2. Merge the branch into `main` (simulating an approved release that carries a runtime defect).

### 2. Observe Smoke Test Failure
1. The pipeline on `main` runs: `test` passes, `deploy` publishes the ledger, but `staging-healthcheck` fails:
   - Smoke test reports `HTTP 500: Unhandled DBConnectionPoolTimeout`.

### 3. Open Incident Issue
1. Open a new issue in GitLab using the template in `.gitlab/issue_templates/incident.md`.
2. Populate the telemetry fields:
   - **Pipeline URL**: URL of the failed pipeline on `main`
   - **Culprit Commit SHA**: SHA of the bad commit from `demo/scenario-c-bad-healthcheck`
   - **MR Number**: Merge request number
   - **Linked Issue Number**: Linked issue number

### 4. Trigger Incident Trace Flow
1. In the incident issue comments, mention `@<incident-flow-handle>`:
   ```text
   @<incident-flow-handle> please investigate root cause and prepare rollback command
   ```

### 5. Expected result (to be confirmed after the first run)
- Flow 3 traces using the incident issue's fields (culprit SHA, MR, linked issue) and available tools.
- The flow posts an incident summary detailing the breaking change, its provenance trailer, and outputs the exact git command:
  ```bash
  git revert <culprit_sha> --no-edit && git push gitlab main
  ```
- Run the command to restore staging health and verify the subsequent pipeline passes.

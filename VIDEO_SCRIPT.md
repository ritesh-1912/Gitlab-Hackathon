# 🎙️ Video Recording Script: <PROJECT_NAME>

**Target Duration**: 2 minutes 40 seconds (Hard limit: < 2:45 / 165 seconds)  
**Hackathon**: GitLab Transcend Hackathon ("Life After Code")  
**Speaker Pace**: ~140 words per minute (Clear, confident, conversational)

---

## 🎬 Minute-by-Minute Teleprompter Script

### [0:00 – 0:20] Hook & Problem (20 Seconds)
**On Screen**: Show the repository `README.md` and the architecture diagram.

> *"Generative AI solved code authoring, but it created an operational crisis. Teams are shipping AI-generated code faster than they can verify intent or trace provenance. When something breaks in production at 2 AM, who wrote it, what requirement authorized it, and which agent assisted it?*
> 
> *This is `<PROJECT_NAME>`: an end-to-end DevSecOps accountability pipeline powered by the GitLab Duo Agent Platform."*

---

### [0:20 – 1:00] Plan & Verify: Intent Flow & Clean MR (40 Seconds)
**On Screen**: Switch to GitLab **Issue #1: "Add Inventory Summary Endpoint"**.

> *"We start in the Plan stage. Before writing a line of code, we mention our Intent Flow on Issue #1."*

**Action**: Post `@intent-agent please establish scope and criteria.`  
**On Screen**: Flow response appears with Acceptance Criteria, Task Checklist, and Out of Scope list.

> *"The agent analyzes the requirements and posts verifiable acceptance criteria, a checklist, and explicit Out-of-Scope guardrails to prevent AI scope creep.*
> 
> *Now, we open a clean feature Merge Request. Notice two things: the commit carries a mandatory Git trailer—`Assisted-by: gitlab-duo`—and the MR description explicitly links `Closes #1`.*
> 
> *Our CI pipeline runs the tests, scans secrets, and executes our custom `accountability-gate`."*

---

### [1:00 – 1:35] Review & Release: Accountability Card & Pages (35 Seconds)
**On Screen**: Switch to MR #1 comment thread.

> *"For review, we mention our Accountability Card flow."*

**Action**: Post `@accountability-card review`.  
**On Screen**: Flow posts the structured Accountability Card.

> *"Our agent reviews the diff, verifies provenance, confirms acceptance criteria are met, checks for scope creep, and recommends APPROVE. Most importantly, it reminds us: 'Advisory only: a human decides.'*
> 
> *We approve and merge. On main, the deploy stage updates our continuous Accountability Ledger, published statically to GitLab Pages."*

**Action**: Click the `staging` environment URL to show the live HTML table with compliance metrics.

---

### [1:35 – 2:05] Secure & Govern: Catching Bad AI Code (30 Seconds)
**On Screen**: Switch to MR #2 (`demo/scenario-b-bad-gate`).

> *"Now, what happens with unvetted, runaway AI changes? Scenario B introduces a commit missing the provenance trailer, an unrelated backdoor script, and a dummy AWS key.*
> 
> *Watch what happens: GitLab Secret Detection flags the credential, and our `accountability-gate` fails the build, blocking the merge.*
> 
> *The Accountability Card flags the high risk and recommends REJECT. Bad code never touches our default branch."*

---

### [2:05 – 2:35] Monitor & Remediate: Incident Trace (30 Seconds)
**On Screen**: Show failed pipeline on `main` (`staging-healthcheck` failed with HTTP 500).

> *"In production, regressions happen. Here, a broken release failed our post-deploy healthcheck smoke test. We open an incident issue using our structured telemetry template and call our Incident Trace flow."*

**Action**: Post `@incident-trace please investigate root cause and prepare rollback command`.  
**On Screen**: Flow response appears with root-cause analysis and exact `git revert` command.

> *"The agent parses the failed pipeline, traces the regression to the exact culprit commit, identifies its AI provenance, and generates the exact `git revert` command.*
> 
> *We run the revert, and staging is instantly healthy again."*

---

### [2:35 – 2:45] Conclusion: Supervised Autonomy (10 Seconds)
**On Screen**: Return to the **Accountability Ledger** on GitLab Pages showing the complete audit trail.

> *"From planning intent to post-incident remediation, `<PROJECT_NAME>` covers the entire DevSecOps lifecycle on GitLab Duo—keeping humans in the loop every step of the way. Thank you!"*

---

## ⏱️ Speaker Time Markers Checklist
- [ ] **0:20** — Intro complete, entering Issue #1
- [ ] **1:00** — Intent defined, MR #1 verified, Accountability Card posted
- [ ] **1:35** — MR #1 merged, GitLab Pages Ledger shown
- [ ] **2:05** — Scenario B pipeline failure & rejection shown
- [ ] **2:35** — Incident Trace & `git revert` output shown
- [ ] **2:45** — Final slide / closing statement complete

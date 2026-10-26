# 🚨 Staging Release Incident Report

## Incident Telemetry
- **Pipeline URL**: <!-- Paste failed pipeline URL here, e.g. https://gitlab.com/group/project/-/pipelines/12345 -->
- **Culprit Commit SHA**: <!-- Paste culprit commit SHA here, e.g. a1b2c3d4e5f6... -->
- **MR Number**: <!-- Paste merge request number here, e.g. !5 -->
- **Linked Issue Number**: <!-- Paste original intent issue number here, e.g. #42 -->

## Observed Failure
- **Stage**: `healthcheck`
- **Error Diagnostic**:
  ```text
  CRITICAL: Healthcheck failed! Staging smoke test returned HTTP 500 / unhandled exception.
  Endpoint: GET /health
  ```

## Agent Triage Action
Mention the Incident Trace flow to trigger automated root-cause trace and remediation:
> `@<incident-flow-handle> please investigate root cause and prepare rollback command`

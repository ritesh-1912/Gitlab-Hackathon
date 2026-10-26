# GitLab Duo Agent Platform Reference Documentation

This directory contains the official GitLab documentation and specifications for custom flows and triggers, saved locally to serve as the ground truth for schema validation, toolsets, and execution models.

---

## 1. Document Index

| File | Source URL | Description |
| :--- | :--- | :--- |
| [`custom_flows_schema.md`](custom_flows_schema.md) | [GitLab Docs: Custom flow YAML schema](https://docs.gitlab.com/user/duo_agent_platform/flows/custom_flows_schema/) | YAML structure, restricted fields, goal values by trigger type (`mention`, `assign`, `merge_request`, `pipeline`), and `coding_environment` (`full` vs `none`). |
| [`custom_flows.md`](custom_flows.md) | [GitLab Docs: Custom flows](https://docs.gitlab.com/user/duo_agent_platform/flows/custom/) | Flow creation, execution mechanics, agent components, routing, and UI settings. |
| [`triggers.md`](triggers.md) | [GitLab Docs: Triggers](https://docs.gitlab.com/user/duo_agent_platform/triggers/) | Event triggers (`mention`, `assign`, `reviewer_assigned`, `work_item`, `pipeline`), permissions, and execution rules. |
| [`flow_registry_v1_spec.md`](flow_registry_v1_spec.md) | [GitLab Repo: Flow Registry v1 Specification](https://gitlab.com/gitlab-org/modelops/applied-ml/code-suggestions/ai-assist/-/raw/main/docs/flow_registry/v1.md) | Full architectural specification for flow registry v1 YAML syntax, inputs, routers, and components. |
| [`official_example_flow.md`](official_example_flow.md) | [GitLab Blog: Understanding flows](https://about.gitlab.com/blog/understanding-flows-multi-agent-workflows/) | Official end-to-end multi-agent flow example (`implement_feature`) demonstrating `AgentComponent`, prompt templates, toolsets, and routers. |

---

## 2. Critical Flow Authoring Rules (Addendum Overrides)

1. **Top-Level YAML Schema (v1)**:
   - Required keys: `version`, `environment`, `components`, `prompts`, `routers`, `flow`.
   - Optional key: `coding_environment` (`ambient` environment required; `coding_environment: none` for API-only flows, `full` if repo files are read/written).
   - **RESTRICTED / FORBIDDEN KEYS**: Do NOT include `name`, `description`, or `product_group` at root. Do NOT use `model`, `stop`, or `response_schema_id` inside prompts/components.

2. **Component & Prompt Structure**:
   - Components use `type: AgentComponent`, `prompt_id`, `inputs` (e.g. `from: "context:goal"`, `from: "context:project_id"`), `toolset` list, and `ui_log_events` (`on_agent_final_answer`, `on_tool_execution_success`, `on_tool_execution_failed`).
   - Prompts include `name`, `prompt_id`, `unit_primitives: []`, `prompt_template` (`system`, `user`, `placeholder: history`), and `params: { timeout: 300 }`.
   - Routers connect each component to `to: "end"`.
   - `flow` specifies `entry_point: "<component_name>"`.

3. **Confirmed Toolset Names**:
   The following tools are strictly verified:
   - `get_issue`
   - `get_repository_file`
   - `list_repository_tree`
   - `find_files`
   - `blob_search`
   - `create_file`
   - `create_commit`
   - `create_merge_request`
   - `create_issue_note`
   
   *(Any other tool name—such as MR diff, MR notes, pipeline jobs, job logs, deployments—is marked **VERIFY**. If an unconfirmed tool is not available in the runtime, prompts must use fallbacks or issue notes).*

4. **Trigger Payload Formats**:
   - **Primary Trigger**: Mention (`@<flow-service-account>`). Goal format:
     ```text
     Input: <comment text>
     Context: {Issue IID: N}
     ```
   - **Assign / Reviewer Events**: Goal format may be an IID or typed URL:
     ```text
     Context:
     MergeRequest: https://gitlab.example.com/.../merge_requests/10
     ```
     Prompts must parse both integer IIDs and resource URLs.
   - **Pipeline Event Trigger**: Controlled by feature flag; stretch goal only.

5. **Resource Budgeting & Tracer Bullet**:
   - Flows run as CI jobs and consume GitLab compute/credit units (Budget: 500 credits, max 12 total runs).
   - **Tracer Bullet**: A minimal 15-line flow that posts a single comment on mention must be validated before authoring Flows 1-3.

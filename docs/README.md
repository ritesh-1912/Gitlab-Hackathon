# GitLab Duo Agent Platform Reference Documentation

This directory lists the official GitLab reference documentation and specifications used to design and validate the custom flows, triggers, and CI templates.

---

## 1. Official Documentation Index

| Topic | Official Source URL | Description |
| :--- | :--- | :--- |
| **Custom Flow YAML Schema** | [GitLab Docs: Custom flow YAML schema](https://docs.gitlab.com/user/duo_agent_platform/flows/custom_flows_schema/) | YAML structure, restricted fields, goal values by trigger type (`mention`, `assign`, `merge_request`, `pipeline`), and `coding_environment` (`full` vs `none`). |
| **Custom Flows Guide** | [GitLab Docs: Custom flows](https://docs.gitlab.com/user/duo_agent_platform/flows/custom/) | Flow creation, execution mechanics, agent components, routing, and UI settings. |
| **Triggers Guide** | [GitLab Docs: Triggers](https://docs.gitlab.com/user/duo_agent_platform/triggers/) | Event triggers (`mention`, `assign`, `reviewer_assigned`, `work_item`, `pipeline`), permissions, and execution rules. |
| **Flow Registry v1 Spec** | [GitLab Repo: Flow Registry v1 Specification](https://gitlab.com/gitlab-org/modelops/applied-ml/code-suggestions/ai-assist/-/raw/main/docs/flow_registry/v1.md) | Official architectural specification for Flow Registry v1 YAML syntax, inputs, routers, and components. |
| **Official Example Flow** | [GitLab Blog: Understanding flows](https://about.gitlab.com/blog/understanding-flows-multi-agent-workflows/) | Official end-to-end multi-agent flow example (`implement_feature`) demonstrating `AgentComponent`, prompt templates, toolsets, and routers. |

---

## 2. Key Custom Flow Specifications (Flow Registry v1)

1. **Top-Level YAML Schema (v1)**:
   - Allowed keys: `version: "v1"`, `environment: ambient`, `components`, `prompts`, `routers`, `flow`, and optional `coding_environment: none | full`.
   - **Restricted/Forbidden Keys**: Do NOT include `name`, `description`, or `product_group` at root. Do NOT use `model`, `stop`, or `response_schema_id` inside prompts/components.

2. **Component & Prompt Structure**:
   - Components use `type: AgentComponent`, `prompt_id`, `inputs` (e.g. `from: "context:goal"`, `from: "context:project_id"`), `toolset` list, and `ui_log_events`.
   - Prompts include `name`, `prompt_id`, `unit_primitives: []`, `prompt_template` (`system`, `user`, `placeholder: history`), and `params: { timeout }`.
   - Routers connect each component to `to: "end"`.
   - `flow` specifies `entry_point: "<component_name>"`.

3. **Confirmed Toolset Names**:
   The following tools are confirmed in the platform:
   - `get_issue`
   - `get_repository_file`
   - `list_repository_tree`
   - `find_files`
   - `blob_search`
   - `create_file`
   - `create_commit`
   - `create_merge_request`
   - `create_issue_note`
   *(All other tool names—such as MR diff, MR notes, pipeline job logs—are unconfirmed and treated as optional/VERIFY with fallbacks to confirmed tools).*

4. **Trigger Payload Formats**:
   - **Primary Trigger**: Mention (`@<flow-service-account>`). Goal format:
     ```text
     Input: <comment text>
     Context: {Issue IID: N}
     ```
   - **Assign / Reviewer Events**: Goal format may be an integer IID or typed URL:
     ```text
     Context:
     MergeRequest: https://gitlab.example.com/.../merge_requests/10
     ```
     Prompts must parse both formats.

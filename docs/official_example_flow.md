[Blog](/blog/)

[AI](/blog/categories/ai/)

Understanding flows: Multi-agent workflows

Updated on: May 27, 2026

13 min read

# Understanding flows: Multi-agent workflows

Deep dive into GitLab Duo Agent Platform flows. Learn about foundational flows, create custom user-defined workflows, and learn flow orchestration patterns.

![](https://res.cloudinary.com/about-gitlab-com/image/upload/f_auto,q_auto,c_lfill/v1765809212/noh0mdfn9o94ry9ykura.png)

![Itzik Gan Baruch](https://res.cloudinary.com/about-gitlab-com/image/upload/f_auto,q_auto/v1749658921/Blog/Author%20Headshots/iganbaruch-headshot.jpg)[Itzik Gan Baruch](/blog/authors/itzik-gan-baruch/)

[AI](/blog/tags/ai/)[product](/blog/tags/product/)[features](/blog/tags/features/)[tutorial](/blog/tags/tutorial/)

*Welcome to Part 4 of our eight-part guide, [Getting started with GitLab Duo Agent Platform](/blog/gitlab-duo-agent-platform-complete-getting-started-guide/), where you'll master building and deploying AI agents and workflows within your development lifecycle. Follow tutorials that take you from your first interaction to production-ready automation workflows with full customization.*

**In this article:**

* [What are flows and how do they work?](#introduction-to-flows)
* [Foundational flows provided by GitLab](#foundational-flows)
* [Creating custom flows](#how-to-create-custom-flows)
* [Flow execution and orchestration](#flow-execution)
* [Real-world examples and use cases](#example-custom-flow-yaml)

> 🎯 Try [**GitLab Duo Agent Platform**](https://about.gitlab.com/gitlab-duo-agent-platform/) today!

## Introduction to flows

Flows are combinations of one or more agents collaborating together. They orchestrate multi-step workflows to solve complex problems, and are executed on the GitLab platform compute.

**Key characteristics of flows:**

* **Multi-agent orchestration**: Combine multiple specialized agents
* **Built-in**: Run on platform compute, no extra environment necessary
* **Event-driven**: Triggered by mention, assignment, or assign as reviewer
* **Asynchronous**: Run in background while you continue working
* **Complete workflows**: Handle end-to-end tasks from analysis to implementation

Think of flows as autonomous workflows that can gather context, make decisions, execute changes, and deliver results, all while you focus on other work.

## Flows vs. agents: Understanding the difference

Agents work with you interactively. Flows work for you autonomously.

| Aspect | Agents | Flows |
| --- | --- | --- |
| **Interaction** | Interactive chat | Autonomous execution |
| **When to use** | Questions, guidance, and performing tasks interactively | Autonomous multi-step workflows |
| **User involvement** | Active conversation | Trigger and review results |
| **Execution time** | Real-time responses | Background processing |
| **Complexity** | Single-agent tasks | Multi-agent orchestration |

## Flow types overview

| Type | Interface | Maintainer | Use Case |
| --- | --- | --- | --- |
| **[Foundational](https://docs.gitlab.com/user/duo_agent_platform/flows/foundational_flows/)** | UI actions, IDE interface | GitLab | [Software Development](https://docs.gitlab.com/user/duo_agent_platform/flows/foundational_flows/software_development/), [Developer](https://docs.gitlab.com/user/duo_agent_platform/flows/foundational_flows/developer/), [Fix CI/CD Pipeline](https://docs.gitlab.com/user/duo_agent_platform/flows/foundational_flows/fix_pipeline/), [Convert to GitLab CI/CD](https://docs.gitlab.com/user/duo_agent_platform/flows/foundational_flows/convert_to_gitlab_ci/), [Code Review](https://docs.gitlab.com/user/duo_agent_platform/flows/foundational_flows/code_review/), [SAST Vulnerability Resolution](https://docs.gitlab.com/user/duo_agent_platform/flows/foundational_flows/agentic_sast_vulnerability_resolution/), [SAST false positive detection](https://docs.gitlab.com/user/duo_agent_platform/flows/foundational_flows/sast_false_positive_detection/), [Secret false positive detection](https://docs.gitlab.com/user/duo_agent_platform/flows/foundational_flows/secret_false_positive_detection/) |
| **[Custom](https://docs.gitlab.com/user/duo_agent_platform/flows/custom/)** | Mention, assign, assign reviewer | You | Examples: Larger migration/modernization, release automation, dependency update management |

## Foundational flows

Foundational flows are production-ready workflows created and maintained by GitLab to automate common development tasks.

### Currently available foundational flows

| Flow | Where Available | How Flow Gets Triggered | Best For |
| --- | --- | --- | --- |
| [**Software Development**](https://docs.gitlab.com/user/duo_agent_platform/flows/foundational_flows/software_development/) | IDEs (VS Code, JetBrains, Visual Studio) | Click Flows tab in IDE | Feature implementation, complex refactoring, multi-file changes |
| [**Developer**](https://docs.gitlab.com/user/duo_agent_platform/flows/foundational_flows/developer/) | GitLab Web UI | Mention `@duo-developer-<namespace>` in comment, assign to issue, or click "Generate MR with Duo" button | Well-defined features, bug fixes with clear steps |
| [**Fix CI/CD Pipeline**](https://docs.gitlab.com/user/duo_agent_platform/flows/foundational_flows/fix_pipeline/) | GitLab Web UI | Click "Fix pipeline with Duo" button on failed pipeline | Pipeline debugging, CI/CD configuration issues |
| [**Convert to GitLab CI/CD**](https://docs.gitlab.com/user/duo_agent_platform/flows/foundational_flows/convert_to_gitlab_ci/) | GitLab Web UI | Click "Convert to GitLab CI/CD" button on Jenkinsfile | Jenkins to GitLab CI/CD migration |
| [**Code Review**](https://docs.gitlab.com/user/duo_agent_platform/flows/foundational_flows/code_review/) | GitLab Web UI | Assign or mention `@GitLabDuo` as reviewer on a merge request | Automated code review with AI-native analysis and full SDLC context |
| [**SAST Vulnerability Resolution**](https://docs.gitlab.com/user/duo_agent_platform/flows/foundational_flows/agentic_sast_vulnerability_resolution/) | GitLab Web UI | Runs after a SAST scan on the default branch (high/critical severity). UI access: Click "Resolve with AI" in a vulnerability report | Automatically generate merge requests to resolve SAST vulnerabilities |
| [**SAST false positive detection**](https://docs.gitlab.com/user/duo_agent_platform/flows/foundational_flows/sast_false_positive_detection/) | GitLab Web UI | Runs after a SAST scan on the default branch (critical/high severity). UI access: Click "Check for false positive" in a vulnerability report | Automatically identify and filter false positives in SAST findings |
| [**Secret false positive detection**](https://docs.gitlab.com/user/duo_agent_platform/flows/foundational_flows/secret_false_positive_detection/) | GitLab Web UI | Runs after a secret detection scan on the default branch. UI access: Click "Check for false positive" in a vulnerability report | Automatically identify and filter false positives in secret detection findings |

## Custom flows

Custom flows are workflows you can create for your team's specific needs. Flows are [executed on the GitLab Runner infrastructure](https://docs.gitlab.com/user/duo_agent_platform/flows/execution/) and can be triggered by GitLab events.

> **🎯 Try it now:** [Interactive demo of Custom Flows](https://gitlab.navattic.com/custom-flows) — Explore how to create and configure Custom Flows.

### Why create custom flows?

Custom flows automate repetitive multi-step tasks that are specific to your team's workflow. Unlike foundational flows that serve general purposes, custom flows are tailored to your organization's processes, tools, and requirements.

**Common use cases:**

* **Automated code review**: Multi-stage review process (security scan → quality check → style validation)
* **Compliance checking**: Verify regulatory requirements, license compliance, or security policies on each MR
* **Documentation generation**: Auto-update API docs, README files, or changelogs based on code changes
* **Dependency management**: Weekly security scans, automated updates, and vulnerability reports
* **Custom testing**: Specialized test suites for your tech stack or integration tests

### Real-world example

A fintech company creates a compliance flow that runs on every merge request. When triggered by `@compliance-flow`, the flow executes the following steps:

1. **Security agent** scans code for PCI-DSS violations and checks for exposed sensitive data.
2. **Code review agent** verifies that changes follow secure coding standards and best practices.
3. **Documentation agent** checks that API changes include updated documentation.
4. **Summary agent** aggregates findings and posts a compliance report with pass/fail status.

The entire compliance review happens automatically in 5-10 minutes, providing consistent checks across all merge requests.

### How to trigger custom flows

Custom flows can be triggered in multiple ways:

**1. Via mentions in Issues/MRs:**
Mention the flow in a comment to trigger it. Example for a documentation generation flow:

Copy

```yaml
      @doc-generator Generate API documentation for this feature
```

**2. By assigning the flow to an issue or MR:**
Assign the flow using either:

* **GitLab UI**: Click the "Assign" button on the issue/MR and select the flow
* **Command**: Use the `/assign` command in a comment. Example:

Copy

```yaml
      /assign @doc-generator
```

**3. By assigning the flow as a reviewer:**
Assign the flow as a reviewer on a merge request using either:

* **GitLab UI**: Click the "Assign reviewer" button on the merge request and select the flow
* **Command**: Use the `/assign_reviewer` command in a comment. Example:

Copy

```yaml
      /assign_reviewer @doc-reviewer
```

**4. Via pipeline events:**
Configure the flow to trigger automatically when a pipeline changes state (`created`, `started`, `succeeded`, or `failed`). This is configured when you enable the flow in your project.

> **Note:** Pipeline event triggers are currently behind a feature flag and not yet available to all customers on GitLab.com or Dedicated. Check the [Triggers documentation](https://docs.gitlab.com/user/duo_agent_platform/triggers/) for the latest availability status.

Any of these methods automatically triggers the flow to execute and perform its tasks.

### How to create custom flows

Custom flows are created through the GitLab UI at **AI → Flows → New flow** in your project, or from **Explore → AI Catalog → Flows → New flow**. When creating a flow, you can set its visibility to **Private** (only accessible in your project) or **Public** (available in the AI Catalog for other projects).

After creating a flow, you must **enable** it in your project before it can be triggered. When you enable a flow, you configure which trigger types activate it: **Mention**, **Assign**, **Assign reviewer**, or **Pipeline events**.

You define your flow using YAML configuration that specifies components, prompts, routing, and execution flow. The YAML schema allows you to create sophisticated multi-agent workflows with precise control over agent behavior and orchestration.

**Key elements of a custom flow:**

* **Components**: Define the agents and steps in your workflow
* **Prompts**: Configure AI model behavior and instructions
* **Routers**: Control the flow between components
* **Toolsets**: Specify which GitLab API tools agents can use

### Example custom flow YAML

**Background:** This example shows a feature implementation flow for a travel booking platform. When a developer creates an issue with feature requirements, they can trigger this flow to automatically analyze the requirements, review the codebase, implement the solution, and create a merge request, all without manual intervention.
Here's the YAML configuration:

Copy

```yaml
      version: "v1"
environment: ambient
components:
  - name: "implement_feature"
    type: AgentComponent
    prompt_id: "implementation_prompt"
    inputs:
      - from: "context:goal"
        as: "user_goal"
      - from: "context:project_id"
        as: "project_id"
      - from: "context:inputs.user_rule"
        as: "agents_dot_md"
        optional: true
    toolset:
      - "get_issue"
      - "get_repository_file"
      - "list_repository_tree"
      - "find_files"
      - "blob_search"
      - "create_file"
      - "create_commit"
      - "create_merge_request"
      - "create_issue_note"
    ui_log_events:
      - "on_agent_final_answer"
      - "on_tool_execution_success"
      - "on_tool_execution_failed"

prompts:
  - name: "Cheapflights Feature Implementation"
    prompt_id: "implementation_prompt"
    unit_primitives: []
    prompt_template:
      system: |
        You are an expert full-stack developer specializing in travel booking platforms, specifically Cheapflights.

        Your task is to:
        1. Extract the issue IID from the goal (look for "Issue IID: XX")
        2. Use get_issue with project_id={{project_id}} and issue_iid to retrieve issue details
        3. Analyze the requirements for the flight search feature
        4. Review the existing codebase using list_repository_tree, find_files, and get_repository_file
        5. Design and implement the solution following Cheapflights best practices
        6. Create all necessary code files using create_file (call multiple times for multiple files)
        7. Commit the changes using create_commit
        8. Create a merge request using create_merge_request
        9. Post a summary comment to the issue using create_issue_note with the MR link

        Cheapflights Domain Expertise:
        - Flight search and booking systems (Amadeus, Sabre, Skyscanner APIs)
        - Fare comparison and pricing strategies
        - Real-time availability and inventory management
        - Travel industry UX patterns
        - Performance optimization for high-traffic flight searches

        Code Standards:
        - Clean, maintainable code (TypeScript/JavaScript/Python/React)
        - Proper state management for React components
        - RESTful API endpoints with comprehensive error handling
        - Mobile-first responsive design
        - Proper timezone handling (use moment-timezone or date-fns-tz)
        - WCAG 2.1 accessibility compliance

        Flight-Specific Best Practices:
        - Accurate fare calculations (base fare + taxes + fees + surcharges)
        - Flight duration calculations across timezones
        - Search filter logic (price range, number of stops, airlines, departure/arrival times)
        - Sort algorithms (best value, fastest, cheapest)
        - Handle edge cases: date line crossing, daylight saving time, red-eye flights
        - Currency amounts use proper decimal handling (avoid floating point errors)
        - Dates use ISO 8601 format
        - Flight codes follow IATA standards (3-letter airport codes)

        Implementation Requirements:
        - No TODOs or placeholder comments
        - All functions must be fully implemented
        - Include proper TypeScript types or Python type hints
        - Add JSDoc/docstring comments for all functions
        - Comprehensive error handling and input validation
        - Basic unit tests for critical functions
        - Performance considerations for handling large result sets

        CRITICAL - Your final comment on the issue MUST include:
        - **Implementation Summary**: Brief description of what was implemented
        - **Files Created/Modified**: List of all files with descriptions
        - **Key Features**: Bullet points of main functionality
        - **Technical Approach**: Brief explanation of architecture/patterns used
        - **Testing Notes**: How to test the implementation
        - **Merge Request Link**: Direct link to the created MR (format: [View Merge Request](MR_URL))

        IMPORTANT TOOL USAGE:
        - Extract the issue IID from the goal first (e.g., "Issue IID: 12" means issue_iid=12)
        - Use get_issue with project_id={{project_id}} and issue_iid=<extracted_iid>
        - Create multiple files by calling create_file multiple times (once per file)
        - Use create_commit to commit all files together with a descriptive commit message
        - Use create_merge_request to create the MR and capture the MR URL from the response
        - Use create_issue_note with project_id={{project_id}}, noteable_id=<issue_iid>, and body=<your complete summary with MR link>
        - Make sure to include the MR link in the comment body so users can easily access it

      user: |
        Goal: {{user_goal}}
        Project ID: {{project_id}}

        Please complete the following steps:
        1. Extract the issue IID and retrieve full issue details
        2. Analyze the requirements thoroughly
        3. Review the existing codebase structure and patterns
        4. Implement the feature with production-ready code
        5. Create all necessary files (components, APIs, tests, documentation)
        6. Commit all changes with a clear commit message
        7. Create a merge request
        8. Post a detailed summary comment to the issue including the MR link

      placeholder: history
    params:
      timeout: 300

routers:
  - from: "implement_feature"
    to: "end"

flow:
  entry_point: "implement_feature"
```

**What this flow does:** This flow orchestrates an AI agent to automatically implement a feature by analyzing issue requirements, reviewing the codebase, writing production-ready code with domain expertise, and creating a merge request with a detailed summary comment.

For complete documentation and examples, see:

* [Custom Flows documentation](https://docs.gitlab.com/user/duo_agent_platform/flows/custom/)
* [Flow Registry Framework (YAML Schema)](https://gitlab.com/gitlab-org/modelops/applied-ml/code-suggestions/ai-assist/-/blob/main/docs/flow_registry/v1.md)

## Customizing flow behavior with AGENTS.md

You can customize how flows behave using `AGENTS.md` files following the [agents.md](https://agents.md/) standard. This applies to both foundational and custom flows (excluding Code Review Flow).

With `AGENTS.md`, you can define:

* **Project context**: Repository structure, coding conventions, and style guidelines
* **Directory-specific conventions**: Different rules for different parts of your codebase
* **Build and test instructions**: How to build, test, and deploy your project
* **Custom skills**: Specialized capabilities for your team's workflows

For custom flows, update your flow's YAML configuration to access the `user_rule` context:

Copy

```yaml
      components:
  - name: "my_agent"
    type: AgentComponent
    prompt_id: "my_prompt"
    inputs:
      - from: "context:inputs.user_rule"
        as: "agents_dot_md"
      optional: true
```

By setting `optional: true`, the flow gracefully handles cases where no `AGENTS.md` file exists.

Learn more in [Part 8: Customizing GitLab Duo Agent Platform: Chat rules, prompts, and workflows](/blog/customizing-gitlab-duo-chat-rules-prompts-workflows/).

## Flow execution

Flows run on GitLab platform compute. When triggered by an event (mention, assignment, or button click), a session is created and the flow starts to execute.

### Flow context and inputs

Flows access context about the trigger and GitLab objects through the YAML configuration. Components receive context through the `inputs` field:

* **`context:goal`** — The trigger value, which varies by trigger type:
  + **Mention**: Full comment text and resource context
  + **Assign/Assign reviewer**: The resource IID (issue or merge request ID)
  + **Pipeline events**: Full pipeline event webhook payload
* **`context:project_id`** — The project ID where the flow is triggered.

These context values allow your flow to understand what triggered it and access the relevant GitLab data to perform its task. Your flow components use these values in their `inputs` configuration to process the trigger data.

### Multi-agent flows

Custom flows can include multiple agent components that work together sequentially. The flow's YAML configuration defines:

* **Components**: One or more agents (AgentComponent) or deterministic steps
* **Routers**: Define the flow between components (e.g., from component A to component B to end)
* **Prompts**: Configure each agent's behavior and model

For example, a code review flow might have a security agent, then a quality agent, then an approval agent, with routers connecting them in sequence.

### Monitoring flow execution

To view flows that are running for your project:

1. Navigate to **AI → Sessions**.
2. Select any session to view more details.
3. The **Details** tab shows a link to the CI/CD job logs.

Sessions show detailed information including step-by-step progress, tool invocations, reasoning, and decision-making process.

### When to use flows

* Complex multi-step tasks
* Background automation
* Event-driven workflows
* Multi-file changes
* Tasks that take time
* Automated reviews/checks

## What's next?

You now understand flows, how to create them, and when to use them vs. agents. Next, learn how to discover, create, and share agents and flows across your organization in [Part 5: AI Catalog](/blog/ai-catalog-discover-and-share-agents/). Explore the AI Catalog to browse available flows and agents, add them to your projects, and publish your own agents and flows.

## Resources

* [GitLab Duo Agent Platform Flows](https://docs.gitlab.com/user/duo_agent_platform/flows/)
* [Foundational Flows documentation](https://docs.gitlab.com/user/duo_agent_platform/flows/foundational_flows/)
* [Custom Flows documentation](https://docs.gitlab.com/user/duo_agent_platform/flows/custom/)
* [Flow execution configuration](https://docs.gitlab.com/user/duo_agent_platform/flows/execution/)
* [GitLab CI/CD Variables guide](https://docs.gitlab.com/ci/variables/)
* [Service Accounts](https://docs.gitlab.com/user/profile/service_accounts/)

---

**Next:** [Part 5: AI Catalog](/blog/ai-catalog-discover-and-share-agents/)

**Previous:** [Part 3: Understanding agents](/blog/understanding-agents-foundational-custom-external/)

## Start your free 30-day GitLab trial

* GitLab Duo Agent Platform access
* Try our most advanced features
* Automate complex tasks with AI

[Get free trial](https://gitlab.com/-/trials/new?glm_content=default-saas-trial&glm_source=about.gitlab.com/blog/)

No credit card required.

## More to explore

[View all blog posts](/blog/)

[AI

![](https://res.cloudinary.com/about-gitlab-com/image/upload/f_auto,q_auto/v1772564423/mvuznp7fepbt6payidvm.png)

### Three developer tasks worth handing to an agent

Read the blog](/blog/three-developer-tasks-worth-handing-to-an-agent/) [AI

![](https://res.cloudinary.com/about-gitlab-com/image/upload/f_auto,q_auto/v1791993648/t2kod74bclspits5cc5o.png)

### Get every merge request in front of the right reviewer, faster

Read the blog](/blog/recommend-reviewers-flow/) [AI

![](https://res.cloudinary.com/about-gitlab-com/image/upload/f_auto,q_auto/v1791993648/t2kod74bclspits5cc5o.png)

### Connect your agents to your software lifecycle with the GitLab MCP server

Read the blog](/blog/mcp-server-ga/)

## We want to hear from you

Enjoyed reading this blog post or have questions or feedback? Share your thoughts by creating a new topic in the GitLab community forum.

[Share your feedback](https://forum.gitlab.com/)

## Start building faster today

See what your team can do with the intelligent orchestration platform for DevSecOps.

[Get your free trial](https://gitlab.com/-/trial_registrations/new?glm_content=default-saas-trial&glm_source=about.gitlab.com/blog/understanding-flows-multi-agent-workflows) [Contact sales](/sales/)
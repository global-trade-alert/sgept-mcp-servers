# METIS MCP — Workflow Engine (ARCHIVED, superseded by Phase 3 `jfm.py` + Linear)

> **Status (2026-04-20): archived.** This server was built against Linear
> ticket JF-270 as a local SQLite-backed state machine for Claude Code
> workflows. The Metis Phase 3 Chief-of-Staff architecture replaced it: the
> state machine is `jf-metis/scripts/jfm.py` and state lives in Linear
> JF-METIS issues (prefix `JFM`, `cos:*` label vocabulary). The Phase 3
> adversarial challenge (JCC-335) explicitly rejected any local state store:
> "all jobs and tasks are always tracked and consistently tracked through
> linear."
>
> **Why archived, not deleted:** the capability-registry angle (JF-273/275)
> is still interesting — a registry MCP that answers "what skills and agents
> does SGEPT have?" could be useful independent of workflow execution. If
> that's ever built, this server is a working starting point (103 passing
> tests at time of archive). The workflow-engine path is closed.
>
> **Do not deploy this to Metis.** The Metis server uses the Phase 3 path.
> Deploying this would create two sources of truth. See
> `~/.gstack/projects/johannesfritz-jf-metis/johannesfritz-main-design-20260417-082424.md`
> for the chosen architecture.

Deterministic workflow engine for Claude Code, exposed via the MCP protocol.

## What it does (historical)

METIS loads workflow definitions from YAML files and provides MCP tools to start, advance, and monitor workflow instances. Each step has a quality gate that validates output before allowing progression.

## Quick start

```bash
# Install
cd metis-mcp
uv sync

# Run tests
uv run pytest tests/ -v

# Start the server
METIS_WORKFLOWS_DIR=/path/to/workflows uv run metis-mcp
```

## MCP Tools

| Tool | Description |
|------|-------------|
| `metis_list_workflows` | List available workflow definitions |
| `metis_start_workflow` | Start a new workflow instance |
| `metis_advance` | Complete current step and advance |
| `metis_get_state` | Get full instance state |
| `metis_list_instances` | List instances with optional filters |

## Configuration

| Env Var | Default | Purpose |
|---------|---------|---------|
| `METIS_WORKFLOWS_DIR` | (none) | Directory containing *.yaml workflow definitions |
| `METIS_AUDIT_DIR` | `~/.metis/audit/` | Directory for JSON lines audit log |

## Workflow YAML format

```yaml
id: my-workflow
name: "My Workflow"
version: 1
steps:
  - id: step_one
    name: "First Step"
    actor: human
    inputs:
      - name: brief
        required: true
    outputs:
      - name: result
        required: true
    gate:
      type: schema
      schema:
        required: [result]
    next: [step_two]
  - id: step_two
    name: "Second Step"
    actor: agent:general
    outputs:
      - name: final_output
        required: true
    gate:
      type: schema
      schema:
        required: [final_output]
    next: []
```

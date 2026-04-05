# METIS MCP - Workflow Engine

Deterministic workflow engine for Claude Code, exposed via the MCP protocol.

## What it does

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

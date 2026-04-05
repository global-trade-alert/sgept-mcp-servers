"""METIS MCP Server - Deterministic workflow engine exposed via MCP protocol."""

import json
import os
import sys
import logging
from typing import Any, Optional

from mcp.server.fastmcp import FastMCP

from .engine import (
    EngineError,
    InstanceNotFoundError,
    InvalidAdvanceError,
    WorkflowEngine,
    WorkflowNotFoundError,
)
from .audit import AuditLog

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Initialize MCP server
mcp = FastMCP("metis_mcp")

# Engine instance (initialized in main or by register_engine_tools)
engine = WorkflowEngine()


def register_engine_tools(mcp_server: FastMCP, eng: WorkflowEngine) -> None:
    """Register all workflow engine tools on the MCP server.

    Uses a registration pattern so other modules (e.g. registry)
    can add tools without merge conflicts.
    """

    @mcp_server.tool(
        name="metis_list_workflows",
        annotations={
            "title": "List Available Workflows",
            "readOnlyHint": True,
            "destructiveHint": False,
            "idempotentHint": True,
            "openWorldHint": False,
        },
    )
    async def metis_list_workflows() -> str:
        """List all available workflow definitions.

        Returns workflow IDs, names, versions, and step summaries.
        Use this to discover what workflows can be started.
        """
        workflows = eng.list_workflows()
        return json.dumps(workflows, indent=2)

    @mcp_server.tool(
        name="metis_start_workflow",
        annotations={
            "title": "Start a Workflow",
            "readOnlyHint": False,
            "destructiveHint": False,
            "idempotentHint": False,
            "openWorldHint": False,
        },
    )
    async def metis_start_workflow(
        workflow_id: str,
        inputs: dict[str, Any],
        actor: Optional[str] = None,
    ) -> str:
        """Start a new workflow instance.

        Args:
            workflow_id: ID of the workflow definition to start
            inputs: Initial inputs required by the first step
            actor: Optional actor identifier (e.g. 'human', 'agent:general')

        Returns instance_id and current step details.
        """
        try:
            instance = eng.start_workflow(workflow_id, inputs, actor)
            state = eng.get_state(instance.instance_id)
            return json.dumps(state, indent=2)
        except (WorkflowNotFoundError, InvalidAdvanceError) as e:
            return json.dumps({"error": str(e)})

    @mcp_server.tool(
        name="metis_advance",
        annotations={
            "title": "Advance Workflow Step",
            "readOnlyHint": False,
            "destructiveHint": False,
            "idempotentHint": False,
            "openWorldHint": False,
        },
    )
    async def metis_advance(
        instance_id: str,
        step_output: dict[str, Any],
    ) -> str:
        """Advance a workflow instance by completing the current step.

        Validates step output against the quality gate. If the gate
        passes, moves to the next step. If it fails, returns errors.

        Args:
            instance_id: UUID of the workflow instance
            step_output: Output data from completing the current step

        Returns next step details, completion status, or gate failure.
        """
        try:
            result = eng.advance(instance_id, step_output)
            return json.dumps(result, indent=2)
        except (InstanceNotFoundError, InvalidAdvanceError, EngineError) as e:
            return json.dumps({"error": str(e)})

    @mcp_server.tool(
        name="metis_get_state",
        annotations={
            "title": "Get Workflow State",
            "readOnlyHint": True,
            "destructiveHint": False,
            "idempotentHint": True,
            "openWorldHint": False,
        },
    )
    async def metis_get_state(instance_id: str) -> str:
        """Get the full state of a workflow instance.

        Args:
            instance_id: UUID of the workflow instance

        Returns complete instance state including step states and outputs.
        """
        try:
            state = eng.get_state(instance_id)
            return json.dumps(state, indent=2)
        except InstanceNotFoundError as e:
            return json.dumps({"error": str(e)})

    @mcp_server.tool(
        name="metis_list_instances",
        annotations={
            "title": "List Workflow Instances",
            "readOnlyHint": True,
            "destructiveHint": False,
            "idempotentHint": True,
            "openWorldHint": False,
        },
    )
    async def metis_list_instances(
        status: Optional[str] = None,
        workflow_id: Optional[str] = None,
    ) -> str:
        """List workflow instances, optionally filtered by status or workflow.

        Args:
            status: Filter by status ('running', 'completed', 'failed', 'blocked')
            workflow_id: Filter by workflow definition ID

        Returns list of matching workflow instances.
        """
        instances = eng.list_instances(status=status, workflow_id=workflow_id)
        return json.dumps(instances, indent=2)


# Register engine tools on the module-level server and engine
register_engine_tools(mcp, engine)

# Register registry tools
from .registry import CapabilityRegistry, register_registry_tools

registry_dir = os.environ.get("METIS_REGISTRY_DIR")
if registry_dir:
    registry = CapabilityRegistry(registry_dir)
    registry.load()
    register_registry_tools(mcp, registry)
    logger.info(f"Loaded {len(registry._entries)} registry entries from {registry_dir}")
else:
    logger.info("No METIS_REGISTRY_DIR set — registry tools disabled")


def main() -> None:
    """Run the MCP server."""
    # Load workflows from configured directory
    workflows_dir = os.environ.get("METIS_WORKFLOWS_DIR")

    # Also check command line args
    if not workflows_dir and len(sys.argv) > 1:
        for i, arg in enumerate(sys.argv[1:], 1):
            if arg == "--workflows-dir" and i < len(sys.argv) - 1:
                workflows_dir = sys.argv[i + 1]
                break
            elif arg.startswith("--workflows-dir="):
                workflows_dir = arg.split("=", 1)[1]
                break

    if workflows_dir:
        try:
            count = engine.load_workflows(workflows_dir)
            logger.info(f"Loaded {count} workflow(s) from {workflows_dir}")
        except EngineError as e:
            logger.error(f"Failed to load workflows: {e}")
            sys.exit(1)
    else:
        logger.warning(
            "No workflows directory configured. "
            "Set METIS_WORKFLOWS_DIR or use --workflows-dir"
        )

    logger.info("Starting METIS MCP Server")
    mcp.run()


if __name__ == "__main__":
    main()

"""MCP server for GTA monitoring and automated review (Sancho Claudino)."""

import os
from mcp.server import Server
from mcp.server.stdio import stdio_server

from .auth import JWTAuthManager
from .api import GTAAPIClient
from .source_fetcher import SourceFetcher
from .constants import SANCHO_USER_ID, SANCHO_FRAMEWORK_ID
from .formatters import (
    format_step1_queue,
    format_measure_detail,
    format_source_result,
    format_templates
)


# Initialize FastMCP server
server = Server("gta-mnt")

# Global singletons (will be initialized in main)
auth_manager: JWTAuthManager
api_client: GTAAPIClient
source_fetcher: SourceFetcher


@server.list_tools()
async def list_tools():
    """List available MCP tools."""
    return [
        {
            "name": "gta_mnt_list_step1_queue",
            "description": (
                "List measures awaiting Step 1 review, ordered by status_time DESC "
                "(most recent first). Uses api_state_act_status_log for accurate ordering."
            ),
            "inputSchema": {
                "type": "object",
                "properties": {
                    "limit": {"type": "number", "description": "Max measures to return (1-100)", "default": 20},
                    "offset": {"type": "number", "description": "Offset for pagination", "default": 0},
                    "implementing_jurisdictions": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Filter by jurisdiction codes (e.g., ['USA', 'CHN'])"
                    },
                    "date_entered_review_gte": {
                        "type": "string",
                        "description": "Filter by date entered review (YYYY-MM-DD)"
                    }
                }
            }
        },
        {
            "name": "gta_mnt_get_measure",
            "description": (
                "Get complete StateAct details including all interventions, comments, "
                "and source references for validation."
            ),
            "inputSchema": {
                "type": "object",
                "properties": {
                    "state_act_id": {"type": "number", "description": "StateAct ID"},
                    "include_interventions": {"type": "boolean", "description": "Include nested interventions", "default": True},
                    "include_comments": {"type": "boolean", "description": "Include existing comments", "default": True}
                },
                "required": ["state_act_id"]
            }
        },
        {
            "name": "gta_mnt_get_source",
            "description": (
                "Retrieve official source for a StateAct. Priority: S3 archived file, "
                "fallback to URL. Extracts text from PDFs and HTML."
            ),
            "inputSchema": {
                "type": "object",
                "properties": {
                    "state_act_id": {"type": "number", "description": "StateAct ID"},
                    "fetch_content": {"type": "boolean", "description": "Fetch and extract content", "default": True}
                },
                "required": ["state_act_id"]
            }
        },
        {
            "name": "gta_mnt_add_comment",
            "description": (
                "Add a structured review comment to a measure. Supports issue comments, "
                "verification comments, and review complete comments."
            ),
            "inputSchema": {
                "type": "object",
                "properties": {
                    "measure_id": {"type": "number", "description": "StateAct ID"},
                    "comment_text": {"type": "string", "description": "Full comment text (structured per spec)"},
                    "template_id": {"type": "number", "description": "Optional template ID"}
                },
                "required": ["measure_id", "comment_text"]
            }
        },
        {
            "name": "gta_mnt_set_status",
            "description": (
                "Update StateAct status (e.g., to 'Under revision' after issues found). "
                "Creates entry in api_state_act_status_log."
            ),
            "inputSchema": {
                "type": "object",
                "properties": {
                    "state_act_id": {"type": "number", "description": "StateAct ID"},
                    "new_status_id": {"type": "number", "description": "Status ID (2=Step1, 3=Publishable, 6=Under revision)"},
                    "comment": {"type": "string", "description": "Optional reason for status change"}
                },
                "required": ["state_act_id", "new_status_id"]
            }
        },
        {
            "name": "gta_mnt_add_framework",
            "description": (
                "Attach 'sancho claudino review' framework tag to a measure for tracking. "
                "Use this to mark that a measure has been reviewed by Sancho Claudino."
            ),
            "inputSchema": {
                "type": "object",
                "properties": {
                    "state_act_id": {"type": "number", "description": "StateAct ID"},
                    "framework_name": {"type": "string", "description": "Framework name", "default": "sancho claudino review"}
                },
                "required": ["state_act_id"]
            }
        },
        {
            "name": "gta_mnt_list_templates",
            "description": "List available comment templates for standardized feedback.",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "include_checklist": {"type": "boolean", "description": "Include checklist templates", "default": False}
                }
            }
        },
        {
            "name": "gta_mnt_log_review",
            "description": (
                "Save review log to persistent storage. Creates review-log.md with "
                "timestamp, source, fields validated, issues found, and actions taken."
            ),
            "inputSchema": {
                "type": "object",
                "properties": {
                    "state_act_id": {"type": "number", "description": "StateAct ID"},
                    "source_url": {"type": "string", "description": "Source URL used for validation"},
                    "fields_validated": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "List of fields checked"
                    },
                    "issues_found": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "List of issues discovered (empty if none)"
                    },
                    "decision": {"type": "string", "description": "APPROVE or DISAPPROVE"},
                    "actions_taken": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "List of actions (comments posted, status changed, framework added)"
                    }
                },
                "required": ["state_act_id", "source_url", "decision"]
            }
        }
    ]


@server.call_tool()
async def call_tool(name: str, arguments: dict):
    """Handle tool invocations."""
    try:
        # WS2: List Step 1 Queue
        if name == "gta_mnt_list_step1_queue":
            data = await api_client.list_step1_queue(
                limit=arguments.get("limit", 20),
                offset=arguments.get("offset", 0),
                implementing_jurisdictions=arguments.get("implementing_jurisdictions"),
                date_entered_review_gte=arguments.get("date_entered_review_gte")
            )
            formatted = format_step1_queue(data)
            return {"content": [{"type": "text", "text": formatted}]}

        # WS3: Get Measure Detail
        elif name == "gta_mnt_get_measure":
            measure = await api_client.get_measure(
                state_act_id=arguments["state_act_id"],
                include_interventions=arguments.get("include_interventions", True),
                include_comments=arguments.get("include_comments", True)
            )
            formatted = format_measure_detail(measure)
            return {"content": [{"type": "text", "text": formatted}]}

        # WS4: Get Source
        elif name == "gta_mnt_get_source":
            state_act_id = arguments["state_act_id"]
            fetch_content = arguments.get("fetch_content", True)

            # First get measure to retrieve source URLs
            measure = await api_client.get_measure(
                state_act_id=state_act_id,
                include_interventions=False,
                include_comments=False
            )

            # Fetch source using SourceFetcher
            source_result = await source_fetcher.get_source(
                state_act_id=state_act_id,
                measure_data=measure,
                fetch_content=fetch_content
            )

            formatted = format_source_result(source_result)
            return {"content": [{"type": "text", "text": formatted}]}

        # WS6: Set Status
        elif name == "gta_mnt_set_status":
            result = await api_client.set_status(
                state_act_id=arguments["state_act_id"],
                new_status_id=arguments["new_status_id"],
                comment=arguments.get("comment")
            )
            return {
                "content": [
                    {
                        "type": "text",
                        "text": f"✅ {result['message']}\n\nStateAct {result['state_act_id']} → Status {result['new_status_id']}"
                    }
                ]
            }

        # WS5: Add Comment
        elif name == "gta_mnt_add_comment":
            result = await api_client.add_comment(
                measure_id=arguments["measure_id"],
                comment_text=arguments["comment_text"],
                template_id=arguments.get("template_id")
            )
            return {
                "content": [
                    {
                        "type": "text",
                        "text": f"✅ {result['message']}\n\nComment ID: {result['comment_id']}\nAuthor: Sancho Claudino (user_id={SANCHO_USER_ID})"
                    }
                ]
            }

        # WS7: Add Framework
        elif name == "gta_mnt_add_framework":
            result = await api_client.add_framework(
                state_act_id=arguments["state_act_id"],
                framework_name=arguments.get("framework_name", "sancho claudino review")
            )
            return {
                "content": [
                    {
                        "type": "text",
                        "text": f"✅ {result['message']}\n\nFramework ID: {result['framework_id']}"
                    }
                ]
            }

        # Log Review (Persistent Storage)
        elif name == "gta_mnt_log_review":
            from .storage import ReviewStorage
            storage = ReviewStorage()

            log_path = storage.save_log(
                state_act_id=arguments["state_act_id"],
                source_url=arguments["source_url"],
                fields_validated=arguments.get("fields_validated", []),
                issues_found=arguments.get("issues_found", []),
                decision=arguments["decision"],
                actions_taken=arguments.get("actions_taken", [])
            )

            return {
                "content": [
                    {
                        "type": "text",
                        "text": f"✅ Review log saved\n\nStateAct: {arguments['state_act_id']}\nDecision: {arguments['decision']}\nLog: {log_path}"
                    }
                ]
            }

        # WS10: List Templates
        elif name == "gta_mnt_list_templates":
            data = await api_client.list_templates(
                include_checklist=arguments.get("include_checklist", False)
            )
            formatted = format_templates(data)
            return {"content": [{"type": "text", "text": formatted}]}

        else:
            return {
                "content": [
                    {
                        "type": "text",
                        "text": f"Unknown tool: {name}"
                    }
                ]
            }

    except Exception as e:
        return {
            "content": [
                {
                    "type": "text",
                    "text": f"❌ Error executing {name}: {str(e)}"
                }
            ]
        }


def main():
    """Run the MCP server."""
    global auth_manager, api_client, source_fetcher

    # Get credentials from environment
    email = os.getenv("GTA_AUTH_EMAIL")
    password = os.getenv("GTA_AUTH_PASSWORD")

    if not email or not password:
        raise RuntimeError(
            "Missing required environment variables: GTA_AUTH_EMAIL, GTA_AUTH_PASSWORD"
        )

    # Initialize singletons
    auth_manager = JWTAuthManager(email, password)
    api_client = GTAAPIClient(auth_manager)
    source_fetcher = SourceFetcher()

    # Run server
    import asyncio
    asyncio.run(stdio_server(server))


if __name__ == "__main__":
    main()

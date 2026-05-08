"""Module entry point: enables `python -m scrapling_mnt`.

Boots the FastMCP stdio server. Use `.cli` for the non-MCP command-line.
"""

from .server import main


if __name__ == "__main__":
    main()

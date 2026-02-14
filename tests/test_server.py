# tests/test_server.py
"""Basic smoke test for MCP server tool registration."""
from ai4news.server import mcp


def test_server_has_tools():
    assert mcp is not None
    assert mcp.name == "ai4news"

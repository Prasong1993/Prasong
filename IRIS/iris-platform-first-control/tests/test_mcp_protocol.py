"""Real MCP stdio integration test using the official SDK client and CLI."""
import asyncio
import json
import tempfile
import unittest
from pathlib import Path

from mcp import Client, StdioServerParameters


class MCPStdioProtocolTests(unittest.TestCase):
    def test_server_discovers_tools_and_executes_health_and_project_tools(self):
        async def exercise():
            with tempfile.TemporaryDirectory(prefix="iris-mcp-test-") as temp_dir:
                server = StdioServerParameters(
                    command="mcp",
                    args=["run", "runtime/mcp_server.py"],
                    env={
                        "IRIS_DB_PATH": str(Path(temp_dir) / "iris.sqlite3"),
                        # The SDK CLI loads the server module by path; explicitly
                        # preserve the project root so runtime imports resolve.
                        "PYTHONPATH": str(Path.cwd()),
                    },
                )
                async with Client(server, raise_exceptions=True) as client:
                    discovered = await asyncio.wait_for(client.list_tools(), timeout=10)
                    names = {tool.name for tool in discovered.tools}
                    self.assertIn("health", names)
                    self.assertIn("create_project", names)
                    self.assertIn("create_task", names)
                    self.assertIn("get_task", names)

                    health = await asyncio.wait_for(client.call_tool("health", {}), timeout=10)
                    self.assertFalse(health.is_error, json.dumps(health.model_dump(), default=str))
                    health_payload = health.structured_content or health.content
                    self.assertIn("OK", json.dumps(health_payload, default=str))

                    created = await asyncio.wait_for(
                        client.call_tool("create_project", {"name": "MCP protocol test"}),
                        timeout=10,
                    )
                    self.assertFalse(created.is_error, json.dumps(created.model_dump(), default=str))
                    created_payload = created.structured_content or created.content
                    self.assertIn("project_id", json.dumps(created_payload, default=str))

        asyncio.run(exercise())


if __name__ == "__main__":
    unittest.main()

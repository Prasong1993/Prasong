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
                    self.assertIn("get_agent_actions", names)
                    self.assertIn("get_resume_context", names)

                    def payload(result):
                        if result.structured_content:
                            return result.structured_content
                        for item in result.content:
                            text_value = getattr(item, "text", "")
                            if text_value:
                                try:
                                    return json.loads(text_value)
                                except json.JSONDecodeError:
                                    pass
                        return result.content

                    health = await asyncio.wait_for(client.call_tool("health", {}), timeout=10)
                    self.assertFalse(health.is_error, json.dumps(health.model_dump(), default=str))
                    health_payload = health.structured_content or health.content
                    self.assertIn("OK", json.dumps(health_payload, default=str))

                    created = await asyncio.wait_for(
                        client.call_tool("create_project", {"name": "MCP protocol test"}),
                        timeout=10,
                    )
                    self.assertFalse(created.is_error, json.dumps(created.model_dump(), default=str))
                    created_payload = payload(created)
                    self.assertIn("project_id", json.dumps(created_payload, default=str))
                    project_id = created_payload["project_id"]

                    task_result = await asyncio.wait_for(
                        client.call_tool("create_task", {
                            "project_id": project_id,
                            "title": "resume journal protocol test",
                        }),
                        timeout=10,
                    )
                    self.assertFalse(task_result.is_error, json.dumps(task_result.model_dump(), default=str))
                    task_payload = payload(task_result)
                    task_id = task_payload["task_id"]

                    history_result = await asyncio.wait_for(
                        client.call_tool("get_agent_actions", {
                            "task_id": task_id, "session_id": "", "limit": 100,
                        }),
                        timeout=10,
                    )
                    history_text = json.dumps(payload(history_result), default=str)
                    self.assertIn("create_task", history_text)
                    self.assertIn("STARTED", history_text)
                    self.assertIn("FINISHED", history_text)
                    self.assertIn("trace_id", history_text)

                    resume_result = await asyncio.wait_for(
                        client.call_tool("get_resume_context", {"task_id": task_id}),
                        timeout=10,
                    )
                    resume_text = json.dumps(payload(resume_result), default=str)
                    self.assertIn(task_id, resume_text)
                    self.assertIn("recent_agent_actions", resume_text)

        asyncio.run(exercise())


if __name__ == "__main__":
    unittest.main()

#!/usr/bin/env python3
"""End-to-end tests for the public MCP stdio interface and installer."""

import json
import os
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class McpProcess:
    def __init__(self, launcher, env):
        self.process = subprocess.Popen([str(launcher)], stdin=subprocess.PIPE, stdout=subprocess.PIPE, text=True, env=env)
        self.identifier = 0

    def request(self, method, params=None):
        self.identifier += 1
        message = {"jsonrpc": "2.0", "id": self.identifier, "method": method, "params": params or {}}
        self.process.stdin.write(json.dumps(message) + "\n")
        self.process.stdin.flush()
        return json.loads(self.process.stdout.readline())

    def close(self):
        if self.process.stdin and not self.process.stdin.closed:
            self.process.stdin.close()
        self.process.wait(timeout=5)
        if self.process.stdout and not self.process.stdout.closed:
            self.process.stdout.close()
        if self.process.returncode:
            raise AssertionError(f"server exited {self.process.returncode}")


class AgentGanttTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.home = Path(self.tmp.name) / "home"
        self.home.mkdir()
        env = os.environ | {"HOME": str(self.home), "AGENT_GANTT_DB": str(self.home / "data" / "projects.sqlite3")}
        self.mcp = McpProcess(ROOT / "run.sh", env)

    def tearDown(self):
        self.mcp.close()
        self.tmp.cleanup()

    def tool(self, name, arguments=None):
        response = self.mcp.request("tools/call", {"name": name, "arguments": arguments or {}})
        return response["result"]

    def test_protocol_and_valid_plan(self):
        initialized = self.mcp.request("initialize", {"protocolVersion": "2025-06-18"})
        self.assertEqual(initialized["result"]["serverInfo"]["version"], "1.1.0")
        names = {tool["name"] for tool in self.mcp.request("tools/list")["result"]["tools"]}
        self.assertEqual(names, {"create_project", "list_projects", "create_task", "update_task", "add_dependency", "project_view"})
        project = self.tool("create_project", {"name": "Release", "description": "Ship it"})["structuredContent"]
        first = self.tool("create_task", {"project_id": project["project_id"], "title": "Design", "start_date": "2026-10-01", "due_date": "2026-10-02", "progress": 25})["structuredContent"]
        second = self.tool("create_task", {"project_id": project["project_id"], "title": "Build", "status": "in_progress"})["structuredContent"]
        dependency = self.tool("add_dependency", {"task_id": second["task_id"], "depends_on_id": first["task_id"]})["structuredContent"]
        self.assertEqual(dependency["task_id"], second["task_id"])
        self.assertEqual(self.tool("update_task", {"task_id": second["task_id"], "progress": 50})["structuredContent"]["updated"], ["progress"])
        view = self.tool("project_view", {"project_id": project["project_id"]})["structuredContent"]
        self.assertEqual(len(view["tasks"]), 2)
        self.assertEqual(view["dependencies"], [{"task_id": second["task_id"], "depends_on_id": first["task_id"]}])

    def test_invalid_references_dates_and_cycles_are_rejected(self):
        self.assertTrue(self.tool("create_task", {"project_id": 999, "title": "missing"})["isError"])
        project = self.tool("create_project", {"name": "Plan"})["structuredContent"]
        first = self.tool("create_task", {"project_id": project["project_id"], "title": "A"})["structuredContent"]
        second = self.tool("create_task", {"project_id": project["project_id"], "title": "B"})["structuredContent"]
        invalid_dates = {"project_id": project["project_id"], "title": "bad", "start_date": "2026-10-03", "due_date": "2026-10-02"}
        self.assertTrue(self.tool("create_task", invalid_dates)["isError"])
        self.assertTrue(self.tool("add_dependency", {"task_id": first["task_id"], "depends_on_id": first["task_id"]})["isError"])
        self.tool("add_dependency", {"task_id": second["task_id"], "depends_on_id": first["task_id"]})
        self.assertTrue(self.tool("add_dependency", {"task_id": first["task_id"], "depends_on_id": second["task_id"]})["isError"])

    def test_installer_works_from_a_downloaded_copy(self):
        self.mcp.close()
        download = Path(self.tmp.name) / "downloaded-agent-gantt"
        shutil.copytree(ROOT, download, ignore=shutil.ignore_patterns(".git", "__pycache__", "tests"))
        install_home = Path(self.tmp.name) / "installed-home"
        target = install_home / ".local" / "share" / "agent-gantt"
        completed = subprocess.run([str(download / "install.sh")], cwd=download, env=os.environ | {"HOME": str(install_home)}, capture_output=True, text=True, check=True)
        self.assertIn(f"installed at {target}", completed.stdout)
        self.assertTrue((target / "run.sh").is_file())
        installed = McpProcess(target / "run.sh", os.environ | {"HOME": str(install_home), "AGENT_GANTT_DB": str(install_home / "data" / "installed.sqlite3")})
        self.assertEqual(installed.request("initialize")["result"]["serverInfo"]["name"], "agent-gantt")
        installed.close()


if __name__ == "__main__":
    unittest.main(verbosity=2)

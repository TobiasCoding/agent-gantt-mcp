# agent-gantt

<p align="center">
  <img src="gantt-mcp-logo.png" alt="agent-gantt logo" width="260">
</p>

agent-gantt is a dependency-free Model Context Protocol server for maintaining
small project plans that AI agents can render as Gantt charts. State lives in
SQLite and the server communicates over MCP stdio.

## Features

- Projects, tasks, assignees, status, progress, and date ranges.
- Explicit same-project task dependencies; nonexistent tasks and dependency cycles
  are rejected.
- Gantt-friendly project view with tasks and dependency edges.
- Python 3.9+ and its standard library only. No package installation or network
  service is required.

## Install

Requires Python 3.9+ and [`uv`](https://docs.astral.sh/uv/). Register the package directly from GitHub with the MCP client’s normal stdio configuration. The first launch installs the package in an isolated environment; no repository checkout or custom installer is needed.

```sh
# Claude Code
claude mcp add -s user agent-gantt -- uvx --from git+https://github.com/TobiasCoding/agent-gantt-mcp.git agent-gantt

# Codex CLI
codex mcp add agent-gantt -- uvx --from git+https://github.com/TobiasCoding/agent-gantt-mcp.git agent-gantt
```

The default database is `~/.local/state/agent-gantt/projects.sqlite3`. To share a database across clients, add `AGENT_GANTT_DB` to that server’s MCP `env` configuration (or use the client CLI’s environment option).

## Tools

- create_project, list_projects
- create_task, update_task
- add_dependency
- project_view returns all tasks and dependency edges in a Gantt-friendly structure.

Dates are ISO dates (YYYY-MM-DD). Valid status values are todo, in_progress,
blocked, and done.

## Data and privacy

The repository contains no project, task, or timeline data. At runtime, data is
written to ~/.local/state/agent-gantt/projects.sqlite3 by default; it is
intentionally ignored by Git. Treat that database as sensitive if it contains
planning information. Set AGENT_GANTT_DB to choose another durable location.

## License

MIT. See LICENSE.

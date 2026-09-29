# agent-gantt

<p align="center">
  <img src="gantt-mcp-logo.png" alt="agent-gantt logo" width="260">
</p>

`agent-gantt` is a dependency-free [Model Context Protocol](https://modelcontextprotocol.io/) server for maintaining small project plans that AI agents can render as Gantt charts. State lives in SQLite and the server communicates over MCP stdio.

## Features

- Projects, tasks, assignees, status, progress, and date ranges
- Explicit task dependencies
- Gantt-friendly project view with tasks and dependency edges
- Python standard library only — no package installation or network service required

## Install

Requires Python 3.9+ and no third-party packages. Clone the repository and register its launcher:

```sh
git clone https://github.com/<owner>/agent-gantt.git
cd agent-gantt
```

```sh
claude mcp add -s user agent-gantt -- "$(pwd)/run.sh"
codex mcp add agent-gantt -- "$(pwd)/run.sh"
```

By default its database is `~/.local/state/agent-gantt/projects.sqlite3`. To use a specific durable/shared path:

```sh
claude mcp add -s user agent-gantt -e AGENT_GANTT_DB=/srv/agent-gantt/projects.sqlite3 -- /absolute/path/to/agent-gantt/run.sh
codex mcp add agent-gantt --env AGENT_GANTT_DB=/srv/agent-gantt/projects.sqlite3 -- /absolute/path/to/agent-gantt/run.sh
```

## Tools

- `create_project`, `list_projects`
- `create_task`, `update_task`
- `add_dependency`
- `project_view` — returns all tasks and dependency edges in a Gantt-friendly structure.

Dates are ISO dates (`YYYY-MM-DD`). Valid status values are `todo`, `in_progress`, `blocked`, and `done`.

## Data and privacy

The repository contains no project, task, or timeline data. At runtime, data is written to `~/.local/state/agent-gantt/projects.sqlite3` by default; it is intentionally ignored by Git. Treat that database as sensitive if it contains planning information. Set `AGENT_GANTT_DB` to choose another durable location.

## License

MIT. See [LICENSE](LICENSE).

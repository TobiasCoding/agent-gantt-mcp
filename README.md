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

Download or clone a release, then run its installer as your normal user:
    git clone https://github.com/TobiasCoding/agent-gantt-mcp.git
    cd agent-gantt-mcp
    ./install.sh

It installs the launcher and server into ~/.local/share/agent-gantt (or
$XDG_DATA_HOME/agent-gantt) and prints the registration commands. Use another
absolute location if needed:

    ./install.sh --prefix "$HOME/.local/share/agent-gantt"

Register the installed launcher with your MCP client:

    codex mcp add agent-gantt -- ~/.local/share/agent-gantt/run.sh
    claude mcp add -s user agent-gantt -- ~/.local/share/agent-gantt/run.sh

To store data in a specific durable/shared path, set AGENT_GANTT_DB in the MCP
client configuration:

    codex mcp add agent-gantt --env AGENT_GANTT_DB=/srv/agent-gantt/projects.sqlite3 -- ~/.local/share/agent-gantt/run.sh
    claude mcp add -s user agent-gantt -e AGENT_GANTT_DB=/srv/agent-gantt/projects.sqlite3 -- ~/.local/share/agent-gantt/run.sh

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

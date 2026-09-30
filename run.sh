#!/usr/bin/env sh
# MCP stdio launcher. The server itself has no third-party dependencies.
set -eu

script_dir=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
server="$script_dir/server.py"

if [ ! -f "$server" ]; then
  printf '%s\n' "agent-gantt: server.py was not found next to run.sh" >&2
  exit 1
fi

if ! command -v python3 >/dev/null 2>&1; then
  printf '%s\n' "agent-gantt: Python 3.9 or newer is required" >&2
  exit 1
fi

exec python3 "$server"

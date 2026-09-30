#!/usr/bin/env sh
# Install a downloaded agent-gantt directory into the current user's data home.
set -eu

usage() {
  printf '%s\n' "Usage: ./install.sh [--prefix DIRECTORY]"
  printf '%s\n' "Installs to ~/.local/share/agent-gantt by default."
}

prefix=${AGENT_GANTT_HOME:-"${XDG_DATA_HOME:-"$HOME/.local/share"}/agent-gantt"}
if [ "${1:-}" = "--prefix" ]; then
  [ $# -eq 2 ] || { usage >&2; exit 2; }
  prefix=$2
elif [ $# -ne 0 ]; then
  usage >&2
  exit 2
fi

case "$prefix" in
  /*) ;;
  *) printf '%s\n' "agent-gantt: --prefix must be an absolute path" >&2; exit 2 ;;
esac

source_dir=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
for file in server.py run.sh README.md LICENSE; do
  [ -f "$source_dir/$file" ] || { printf '%s\n' "agent-gantt: missing $file in downloaded package" >&2; exit 1; }
done

parent_dir=$(dirname -- "$prefix")
mkdir -p "$parent_dir"
stage_dir=$(mktemp -d "$parent_dir/.agent-gantt.XXXXXX")
cleanup() { rm -rf "$stage_dir"; }
trap cleanup EXIT HUP INT TERM

cp "$source_dir/server.py" "$source_dir/run.sh" "$source_dir/README.md" "$source_dir/LICENSE" "$stage_dir/"
[ -f "$source_dir/gantt-mcp-logo.png" ] && cp "$source_dir/gantt-mcp-logo.png" "$stage_dir/"
chmod 755 "$stage_dir/run.sh"

if [ -e "$prefix" ]; then
  backup_dir="$prefix.previous.$$"
  mv "$prefix" "$backup_dir"
  if ! mv "$stage_dir" "$prefix"; then
    mv "$backup_dir" "$prefix"
    exit 1
  fi
  rm -rf "$backup_dir"
else
  mv "$stage_dir" "$prefix"
fi
trap - EXIT HUP INT TERM

printf '%s\n' "agent-gantt installed at $prefix"
printf '%s\n' "Register it with:"
printf '%s\n' "  codex mcp add agent-gantt -- $prefix/run.sh"
printf '%s\n' "  claude mcp add -s user agent-gantt -- $prefix/run.sh"

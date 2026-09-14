#!/usr/bin/env bash
set -eu

# Run one blocking headless Cursor turn. The JSON result object goes to stdout;
# its .session_id resumes the conversation in a later call.
# Usage: cursor-headless.sh PROMPT [SESSION_ID]

usage() {
  echo 'Usage: cursor-headless.sh PROMPT [SESSION_ID]' >&2
  exit 2
}

if [[ $# -lt 1 || $# -gt 2 ]]; then usage; fi
if [[ -z "${1:-}" || "$1" == -* ]]; then usage; fi
if [[ $# -eq 2 && ( -z "${2:-}" || "$2" == -* ) ]]; then usage; fi

args=(-p --force --output-format json)
if [[ $# -eq 2 ]]; then
  args+=(--resume "$2")
fi

exec cursor-agent "${args[@]}" "$1"

#!/usr/bin/env bash
set -eu

if [[ $# -lt 1 || $# -gt 2 || -z "${1:-}" || "$1" == -* ]]; then
  echo 'Usage: watch-paseo.sh AGENT_ID [HOST]' >&2
  exit 2
fi

args=(wait "$1" --json)
if [[ $# -eq 2 ]]; then
  args+=(--host "$2")
fi
exec paseo "${args[@]}"

#!/usr/bin/env bash
set -euo pipefail

if [[ $# -lt 1 || $# -gt 2 ]]; then
  echo "Usage: $0 <url> [timeout-seconds]" >&2
  exit 2
fi

url="$1"
timeout="${2:-60}"
deadline=$((SECONDS + timeout))

until curl --silent --show-error --fail --location "$url" >/dev/null; do
  if (( SECONDS >= deadline )); then
    echo "Timed out waiting for ${url}" >&2
    exit 1
  fi
  sleep 2
done

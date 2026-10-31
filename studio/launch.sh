#!/bin/bash
set -euo pipefail
SOURCE_DIR="$(cd "$(dirname "$0")" && pwd)"
exec python3 "$SOURCE_DIR/server.py" "$@"

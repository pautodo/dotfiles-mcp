#!/bin/bash
# MCP server runner script - resolves paths relative to script location
# This allows the .mcp.json to use portable relative paths

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_PYTHON="$SCRIPT_DIR/venv/bin/python"
SERVER_SCRIPT="$SCRIPT_DIR/server.py"

# Check if venv exists
if [ ! -f "$VENV_PYTHON" ]; then
    echo "Error: Virtual environment not found at $VENV_PYTHON" >&2
    echo "Please run: cd $SCRIPT_DIR && python -m venv venv && ./venv/bin/pip install -r requirements.txt" >&2
    exit 1
fi

exec "$VENV_PYTHON" "$SERVER_SCRIPT"

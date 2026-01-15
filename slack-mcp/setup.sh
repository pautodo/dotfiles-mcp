#!/bin/bash
# Slack MCP Server Setup Script
# Run this script to set up the Slack MCP server for Claude Code

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_DIR="$SCRIPT_DIR/venv"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
MCP_JSON="$PROJECT_ROOT/.mcp.json"

echo "=== Slack MCP Server Setup ==="
echo ""

# Step 1: Create virtual environment
echo "[1/4] Setting up Python virtual environment..."
if [ ! -d "$VENV_DIR" ]; then
    python3 -m venv "$VENV_DIR"
    echo "  - Created virtual environment at $VENV_DIR"
else
    echo "  - Virtual environment already exists"
fi

# Step 2: Install dependencies
echo "[2/4] Installing dependencies..."
source "$VENV_DIR/bin/activate"
pip install -q --upgrade pip
pip install -q -r "$SCRIPT_DIR/requirements.txt"
echo "  - Dependencies installed"

# Step 3: Check for Slack Bot Token
echo "[3/4] Checking Slack configuration..."
if [ -z "$SLACK_BOT_TOKEN" ]; then
    echo ""
    echo "  WARNING: SLACK_BOT_TOKEN environment variable is not set."
    echo ""
    echo "  To configure Slack:"
    echo "  1. Create a Slack App at https://api.slack.com/apps"
    echo "  2. Add Bot Token Scopes: channels:read, channels:history, chat:write, users:read"
    echo "  3. Install the app to your workspace"
    echo "  4. Copy the Bot User OAuth Token (starts with xoxb-)"
    echo "  5. Set the environment variable:"
    echo "     export SLACK_BOT_TOKEN='xoxb-your-token-here'"
    echo ""
else
    echo "  - SLACK_BOT_TOKEN is configured"
fi

# Step 4: Update .mcp.json
echo "[4/4] Updating MCP configuration..."
PYTHON_PATH="$VENV_DIR/bin/python"
SERVER_PATH="$SCRIPT_DIR/server.py"

# Check if .mcp.json exists
if [ -f "$MCP_JSON" ]; then
    # Check if slack entry already exists
    if grep -q '"slack"' "$MCP_JSON"; then
        echo "  - Slack MCP server already configured in $MCP_JSON"
    else
        # Add slack server to existing config using jq if available
        if command -v jq &> /dev/null; then
            # Create temp file with updated config
            jq --arg python "$PYTHON_PATH" --arg server "$SERVER_PATH" \
               '.mcpServers.slack = {
                  "command": $python,
                  "args": [$server],
                  "env": {
                    "SLACK_BOT_TOKEN": "${SLACK_BOT_TOKEN}",
                    "SLACK_CHANNEL_ALLOWLIST": ""
                  }
                }' "$MCP_JSON" > "$MCP_JSON.tmp" && mv "$MCP_JSON.tmp" "$MCP_JSON"
            echo "  - Added Slack MCP server to $MCP_JSON"
        else
            echo ""
            echo "  Please manually add the following to $MCP_JSON in the 'mcpServers' section:"
            echo ""
            echo '    "slack": {'
            echo "      \"command\": \"$PYTHON_PATH\","
            echo "      \"args\": [\"$SERVER_PATH\"],"
            echo '      "env": {'
            echo '        "SLACK_BOT_TOKEN": "${SLACK_BOT_TOKEN}",'
            echo '        "SLACK_CHANNEL_ALLOWLIST": ""'
            echo '      }'
            echo '    }'
            echo ""
        fi
    fi
else
    # Create new .mcp.json
    cat > "$MCP_JSON" << EOF
{
  "mcpServers": {
    "slack": {
      "command": "$PYTHON_PATH",
      "args": ["$SERVER_PATH"],
      "env": {
        "SLACK_BOT_TOKEN": "\${SLACK_BOT_TOKEN}",
        "SLACK_CHANNEL_ALLOWLIST": ""
      }
    }
  }
}
EOF
    echo "  - Created $MCP_JSON"
fi

echo ""
echo "=== Setup Complete ==="
echo ""
echo "Next steps:"
echo "  1. Set your Slack Bot Token:"
echo "     export SLACK_BOT_TOKEN='xoxb-your-token-here'"
echo ""
echo "  2. (Optional) Set channel allowlist for safety:"
echo "     export SLACK_CHANNEL_ALLOWLIST='general,random,C1234567890'"
echo ""
echo "  3. Restart Claude Code to load the MCP server"
echo ""
echo "  4. Test the connection by asking Claude:"
echo "     'List my Slack channels'"
echo ""

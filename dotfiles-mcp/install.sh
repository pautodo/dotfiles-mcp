#!/bin/bash
# Codespaces Dotfiles Install Script
# GitHub automatically runs this script after cloning the dotfiles repo
# This sets up AWS Athena and Slack MCP servers for Claude Code

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
CLAUDE_CONFIG_DIR="$HOME/.claude"

echo "========================================"
echo "  MCP Servers Setup for Claude Code"
echo "========================================"
echo ""

# Step 1: Install AWS CLI if not present
echo "[1/5] Checking AWS CLI..."
if ! command -v aws &> /dev/null; then
    echo "  Installing AWS CLI..."
    cd /tmp
    curl -s "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip"
    unzip -o -q awscliv2.zip
    sudo ./aws/install --update 2>/dev/null || sudo ./aws/install
    rm -rf aws awscliv2.zip
    cd "$SCRIPT_DIR"
    echo "  AWS CLI installed"
else
    echo "  AWS CLI already installed"
fi

# Step 2: Configure AWS SSO profile
echo "[2/5] Configuring AWS SSO profile..."
AWS_CONFIG_FILE="$HOME/.aws/config"
mkdir -p "$HOME/.aws"
if ! grep -q "\[profile voodoo-adn-prod\]" "$AWS_CONFIG_FILE" 2>/dev/null; then
    cat >> "$AWS_CONFIG_FILE" << 'EOF'

[profile voodoo-adn-prod]
sso_start_url = https://voodoo-tech.awsapps.com/start
sso_account_id = 975049923261
sso_role_name = ADNAccessRO
region = eu-west-1
sso_region = eu-west-1
EOF
    echo "  AWS SSO profile added"
else
    echo "  AWS SSO profile already configured"
fi

# Step 3: Setup Athena MCP virtual environment
echo "[3/5] Setting up Athena MCP..."
ATHENA_DIR="$SCRIPT_DIR/athena-mcp"
ATHENA_VENV="$ATHENA_DIR/venv"
if [ -d "$ATHENA_DIR" ]; then
    if [ ! -d "$ATHENA_VENV" ]; then
        python3 -m venv "$ATHENA_VENV"
    fi
    "$ATHENA_VENV/bin/pip" install -q -r "$ATHENA_DIR/requirements.txt"
    echo "  Athena MCP ready"
else
    echo "  Athena MCP directory not found, skipping"
fi

# Step 4: Setup Slack MCP virtual environment
echo "[4/5] Setting up Slack MCP..."
SLACK_DIR="$SCRIPT_DIR/slack-mcp"
SLACK_VENV="$SLACK_DIR/venv"
if [ -d "$SLACK_DIR" ]; then
    if [ ! -d "$SLACK_VENV" ]; then
        python3 -m venv "$SLACK_VENV"
    fi
    "$SLACK_VENV/bin/pip" install -q --upgrade pip
    "$SLACK_VENV/bin/pip" install -q -r "$SLACK_DIR/requirements.txt"
    echo "  Slack MCP ready"
else
    echo "  Slack MCP directory not found, skipping"
fi

# Step 5: Create global Claude MCP configuration
echo "[5/5] Creating global MCP configuration..."
mkdir -p "$CLAUDE_CONFIG_DIR"

cat > "$CLAUDE_CONFIG_DIR/settings.local.json" << EOF
{
  "mcpServers": {
    "athena": {
      "command": "$ATHENA_VENV/bin/python",
      "args": ["$ATHENA_DIR/server.py"],
      "env": {
        "AWS_PROFILE_NAME": "voodoo-adn-prod",
        "AWS_REGION_NAME": "eu-west-1"
      }
    },
    "slack": {
      "command": "$SLACK_VENV/bin/python",
      "args": ["$SLACK_DIR/server.py"],
      "env": {
        "SLACK_BOT_TOKEN": "\${SLACK_BOT_TOKEN}",
        "SLACK_CHANNEL_ALLOWLIST": ""
      }
    }
  }
}
EOF
echo "  Created $CLAUDE_CONFIG_DIR/settings.local.json"

echo ""
echo "========================================"
echo "  Setup Complete!"
echo "========================================"
echo ""
echo "Before using Claude with MCP servers:"
echo ""
echo "  1. AWS Athena - Login to AWS SSO:"
echo "     aws sso login --profile voodoo-adn-prod"
echo ""
echo "  2. Slack - Set your bot token (or add to Codespaces secrets):"
echo "     export SLACK_BOT_TOKEN='xoxb-your-token'"
echo ""
echo "  3. Start Claude Code in any project:"
echo "     claude"
echo ""

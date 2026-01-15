#!/bin/bash
# Athena MCP Server Setup Script for Codespaces
# Run this script to set up the Athena MCP server for Claude Code

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_DIR="$SCRIPT_DIR/venv"

echo "=== Athena MCP Server Setup ==="
echo ""

# Step 1: Install AWS CLI if not present
echo "[1/6] Checking AWS CLI..."
if ! command -v aws &> /dev/null; then
    echo "  - Installing AWS CLI..."
    cd /tmp
    curl -s "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip"
    unzip -o -q awscliv2.zip
    sudo ./aws/install
    rm -rf aws awscliv2.zip
    cd "$SCRIPT_DIR"
    echo "  - AWS CLI installed"
else
    echo "  - AWS CLI already installed: $(aws --version)"
fi

# Step 2: Configure AWS SSO profile
echo "[2/6] Configuring AWS SSO profile..."
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
    echo "  - AWS SSO profile added to $AWS_CONFIG_FILE"
else
    echo "  - AWS SSO profile already configured"
fi

# Step 3: Create virtual environment and install dependencies
echo "[3/6] Setting up Python virtual environment..."
if [ ! -d "$VENV_DIR" ]; then
    python3 -m venv "$VENV_DIR"
    echo "  - Created virtual environment at $VENV_DIR"
else
    echo "  - Virtual environment already exists"
fi

echo "[4/6] Installing dependencies..."
source "$VENV_DIR/bin/activate"
pip install -q -r "$SCRIPT_DIR/requirements.txt"
echo "  - Dependencies installed"

# Step 5: Create .mcp.json in project root
echo "[5/6] Creating MCP configuration..."
PYTHON_PATH="$VENV_DIR/bin/python"
SERVER_PATH="$SCRIPT_DIR/server.py"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
MCP_JSON="$PROJECT_ROOT/.mcp.json"

cat > "$MCP_JSON" << EOF
{
  "mcpServers": {
    "athena": {
      "command": "$PYTHON_PATH",
      "args": ["$SERVER_PATH"],
      "env": {
        "AWS_PROFILE_NAME": "voodoo-adn-prod",
        "AWS_REGION_NAME": "eu-west-1"
      }
    }
  }
}
EOF
echo "  - Created $MCP_JSON"

# Step 6: Summary
echo "[6/6] Verifying setup..."
echo "  - Python: $PYTHON_PATH"
echo "  - Server: $SERVER_PATH"
echo "  - MCP Config: $MCP_JSON"

echo ""
echo "=== Setup Complete ==="
echo ""
echo "Next steps:"
echo "  1. Authenticate with AWS SSO:"
echo "     aws sso login --profile voodoo-adn-prod"
echo ""
echo "  2. Restart Claude Code to load the MCP server:"
echo "     claude"
echo ""
echo "  3. Test the connection by asking Claude:"
echo "     'List all tables in adn_lakehouse_silver'"
echo ""

# Slack MCP Server - Setup Status

> **Last Updated:** January 14, 2026
> **Status:** Implementation complete, awaiting Slack App approval from IT

---

## Token Types

| Token Type | Prefix | Can Read DMs? | Messages Sent As |
|------------|--------|---------------|------------------|
| Bot Token | `xoxb-` | No | Bot name |
| User Token | `xoxp-` | **Yes** | Your name |

**Recommendation:** Request User Token Scopes to access DMs and send messages as yourself.

---

## What Has Been Done

### 1. MCP Server Implementation (Complete)

All code files have been created in `/workspaces/adn-user-journey/mcp-servers/slack-mcp/`:

| File | Description | Status |
|------|-------------|--------|
| `server.py` | Main MCP server with 3 Slack tools | ✅ Created |
| `pyproject.toml` | Python project metadata | ✅ Created |
| `requirements.txt` | Dependencies (slack-sdk, mcp) | ✅ Created |
| `setup.sh` | Installation script | ✅ Created & Executable |
| `run.sh` | Runner script for MCP | ✅ Created & Executable |
| `README.md` | Full documentation | ✅ Created |

### 2. Dependencies Installed (Complete)

Virtual environment created and dependencies installed:
- Location: `mcp-servers/slack-mcp/venv/`
- Packages: `slack-sdk>=3.27.0`, `mcp>=1.0.0`

### 3. MCP Configuration Updated (Complete)

The `.mcp.json` file has been updated to include the Slack server:

```json
{
  "mcpServers": {
    "athena": { ... },
    "slack": {
      "command": "/workspaces/adn-user-journey/mcp-servers/slack-mcp/venv/bin/python",
      "args": ["/workspaces/adn-user-journey/mcp-servers/slack-mcp/server.py"],
      "env": {
        "SLACK_BOT_TOKEN": "${SLACK_BOT_TOKEN}",
        "SLACK_CHANNEL_ALLOWLIST": ""
      }
    }
  }
}
```

### 4. Available Tools

Once activated, the MCP server provides these tools:

| Tool | Description |
|------|-------------|
| `slack_list_channels` | List accessible Slack channels (filtered by allowlist if configured) |
| `slack_read_messages` | Read recent messages from a channel |
| `slack_send_message` | Send a message to a channel |

---

## What Remains To Be Done

### Step 1: Get Slack App Approved by IT (Pending)

**Status:** Waiting for IT team approval

The Slack App needs to be created with these specifications:

**App Name:** Claude Code Bot (or similar)

**Required Bot Token Scopes:**
| Scope | Purpose |
|-------|---------|
| `channels:read` | List public channels |
| `channels:history` | Read messages in public channels |
| `chat:write` | Send messages |
| `users:read` | Resolve user display names |
| `groups:read` | (Optional) List private channels |
| `groups:history` | (Optional) Read private channel messages |

**User Token Scopes (for DM access + sending as yourself):**
| Scope | Purpose |
|-------|---------|
| `im:read` | List your DM conversations |
| `im:history` | **Read your DM messages** |
| `mpim:read` | List group DMs |
| `mpim:history` | Read group DM messages |
| `chat:write` | Send messages as yourself |
| `users:read` | View user profiles |

### Step 2: Set Environment Variable

Once you have the token from Slack:

```bash
# For User Token (recommended - enables DMs + sends as yourself)
export SLACK_BOT_TOKEN='xoxp-your-user-token-here'

# OR for Bot Token (sends as bot, no DM access)
export SLACK_BOT_TOKEN='xoxb-your-bot-token-here'

# Optional: Restrict to specific channels for safety
export SLACK_CHANNEL_ALLOWLIST='general,engineering,C0123456789'
```

### Step 3: Add Bot to Channels

In Slack, for each channel you want Claude to access:
- Open the channel
- Type: `/invite @YourBotName`
- Or: Channel settings → Integrations → Add apps

### Step 4: Restart Claude Code

After setting the environment variable, restart Claude Code to load the MCP server.

### Step 5: Test the Integration

Ask Claude:
- "List my Slack channels"
- "Read the last 10 messages from #general"
- "Send 'Hello!' to #test-channel"

---

## If Starting a New Codespace

The code is already committed/saved. In a new Codespace:

1. **Re-run the setup script** (to recreate the virtual environment):
   ```bash
   cd /workspaces/adn-user-journey/mcp-servers/slack-mcp
   ./setup.sh
   ```

2. **Set the Slack Bot Token** (once you have it from IT):
   ```bash
   export SLACK_BOT_TOKEN='xoxb-your-token-here'
   ```

3. **Restart Claude Code** to load the MCP server.

---

## Troubleshooting

### MCP server not loading
- Check that `SLACK_BOT_TOKEN` is set: `echo $SLACK_BOT_TOKEN`
- Verify venv exists: `ls mcp-servers/slack-mcp/venv/bin/python`
- Re-run setup: `./mcp-servers/slack-mcp/setup.sh`

### "not_in_channel" error
- Bot needs to be added to the channel: `/invite @BotName`

### "missing_scope" error
- Bot token is missing required OAuth scopes
- Go to Slack App settings → OAuth & Permissions → Add missing scope → Reinstall app

### "invalid_auth" error
- Token is invalid or expired
- Generate a new token from Slack app settings

---

## Files Reference

```
mcp-servers/slack-mcp/
├── server.py           # Main MCP server (3 tools)
├── pyproject.toml      # Project metadata
├── requirements.txt    # Dependencies
├── setup.sh            # Installation script (run this in new Codespace)
├── run.sh              # Runner script
├── README.md           # Full documentation
├── SETUP_STATUS.md     # This file
└── venv/               # Virtual environment (recreated by setup.sh)
```

---

## Quick Summary for Claude Code

> **Tell Claude:** "I set up a Slack MCP server. The code is in `mcp-servers/slack-mcp/`.
> I'm waiting for IT to approve the Slack App. Once I have the Bot Token, I need to:
> 1. Run `./mcp-servers/slack-mcp/setup.sh` (if new Codespace)
> 2. Set `SLACK_BOT_TOKEN` environment variable
> 3. Restart Claude Code
> 4. Invite the bot to channels in Slack"

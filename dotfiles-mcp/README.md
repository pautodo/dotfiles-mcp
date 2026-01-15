# MCP Servers Dotfiles

MCP (Model Context Protocol) servers for Claude Code, automatically configured in GitHub Codespaces.

## Quick Start

### One-Time Setup (GitHub Settings)

1. Go to [GitHub Settings > Codespaces](https://github.com/settings/codespaces)
2. Under "Dotfiles", check **"Automatically install dotfiles"**
3. Select this repository
4. Add your Slack token to **Codespaces Secrets**:
   - Name: `SLACK_BOT_TOKEN`
   - Value: `xoxb-your-token`

### In Each New Codespace

Run one command to set everything up:

```bash
~/dotfiles-mcp/install.sh
```

Then authenticate with AWS:

```bash
aws sso login --profile voodoo-adn-prod
```

Start Claude:

```bash
claude
```

## Included MCP Servers

### Athena MCP (AWS Athena)
Query AWS Athena databases directly from Claude Code.

**Tools:**
- `athena_query` - Execute SQL queries
- `athena_list_databases` - List available databases
- `athena_list_tables` - List tables in a database
- `athena_describe_table` - Get table schema

### Slack MCP
Interact with Slack channels from Claude Code.

**Tools:**
- `slack_list_channels` - List accessible channels
- `slack_read_messages` - Read messages from a channel
- `slack_send_message` - Send a message to a channel

## Configuration

The install script creates `~/.claude/settings.local.json` with the MCP server configuration. This works globally across all projects.

### Environment Variables

| Variable | Where to Set | Description |
|----------|--------------|-------------|
| `SLACK_BOT_TOKEN` | Codespaces Secrets | Slack bot OAuth token (xoxb-...) |

### Creating a Slack App

1. Go to https://api.slack.com/apps → "Create New App" → "From scratch"
2. Add Bot Token Scopes: `channels:read`, `channels:history`, `chat:write`, `users:read`
3. Install to workspace and copy the Bot Token
4. Add bot to channels with `/invite @bot-name`

## Troubleshooting

### AWS "ExpiredToken" error
```bash
aws sso login --profile voodoo-adn-prod
```

### Slack "not_in_channel" error
Add the bot to the channel: `/invite @bot-name`

### MCP servers not loading
Restart Claude Code after running `install.sh`

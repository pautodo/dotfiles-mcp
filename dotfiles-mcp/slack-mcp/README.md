# Slack MCP Server

An MCP (Model Context Protocol) server that enables Claude Code to interact with Slack.

## Quick Start

1. Run the setup script:

```bash
cd mcp-servers/slack-mcp
./setup.sh
```

2. Set your Slack Bot Token (see "Creating a Slack App" below):

```bash
export SLACK_BOT_TOKEN='xoxb-your-token-here'
```

3. Restart Claude Code to load the MCP server.

## Creating a Slack App

### Step 1: Create the App

1. Go to https://api.slack.com/apps
2. Click "Create New App"
3. Choose "From scratch"
4. Enter an App Name (e.g., "Claude Code Bot")
5. Select your workspace
6. Click "Create App"

### Step 2: Configure Bot Token Scopes

1. In the left sidebar, click "OAuth & Permissions"
2. Scroll to "Scopes" section
3. Under "Bot Token Scopes", add these scopes:

| Scope | Description |
|-------|-------------|
| `channels:read` | View basic channel info (list channels) |
| `channels:history` | Read messages in public channels |
| `groups:read` | View basic private channel info |
| `groups:history` | Read messages in private channels |
| `chat:write` | Send messages |
| `users:read` | View user profiles (for message display names) |

### Step 3: Install the App

1. Scroll to the top of "OAuth & Permissions"
2. Click "Install to Workspace"
3. Review permissions and click "Allow"
4. Copy the "Bot User OAuth Token" (starts with `xoxb-`)

### Step 4: Add Bot to Channels

The bot can only access channels it has been added to:

1. Open Slack
2. Go to the channel you want the bot to access
3. Click the channel name in the header
4. Click "Integrations" tab
5. Click "Add apps"
6. Find and add your app

Or use the slash command in the channel:
```
/invite @your-bot-name
```

## Configuration

### Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `SLACK_BOT_TOKEN` | Yes | - | Bot User OAuth Token (xoxb-...) |
| `SLACK_CHANNEL_ALLOWLIST` | No | "" (all) | Comma-separated list of allowed channel IDs or names |
| `SLACK_MAX_MESSAGES` | No | 100 | Maximum messages to retrieve per request |

### Channel Allowlist

For safety, you can restrict which channels the bot can access:

```bash
# Allow only specific channels (by name or ID)
export SLACK_CHANNEL_ALLOWLIST="general,random,C0123456789"
```

If not set or empty, the bot can access all channels it has been added to.

## Available Tools

### 1. `slack_list_channels`

List accessible Slack channels.

```
List my Slack channels
```

### 2. `slack_read_messages`

Read recent messages from a channel.

```
Read the last 10 messages from #general
```

### 3. `slack_send_message`

Send a message to a channel.

```
Send "Hello team!" to the #announcements channel
```

## Usage Examples

- "List all Slack channels I have access to"
- "Read the last 20 messages from #engineering"
- "Send a message to #general saying: The deployment is complete"
- "Reply in thread to the last message in #support"

## Troubleshooting

### "not_in_channel" error

The bot needs to be added to the channel. Use `/invite @bot-name` in the channel.

### "missing_scope" error

The bot token is missing required OAuth scopes. Go to your app's OAuth settings and add the missing scope, then reinstall the app.

### "invalid_auth" error

The bot token is invalid or expired. Generate a new token from your Slack app settings.

### Channel not found

Make sure you're using the exact channel name (without #) or the channel ID. Use `slack_list_channels` to see available channels.

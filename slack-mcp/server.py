#!/usr/bin/env python3
"""
Slack MCP Server

An MCP server that provides tools for interacting with Slack.
Requires a Slack Bot Token with appropriate scopes.
"""

import os
from datetime import datetime
from typing import Any

from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent

# =============================================================================
# Configuration
# =============================================================================

SLACK_BOT_TOKEN = os.environ.get("SLACK_BOT_TOKEN")
# Comma-separated list of allowed channel IDs or names (empty = all accessible channels)
SLACK_CHANNEL_ALLOWLIST = os.environ.get("SLACK_CHANNEL_ALLOWLIST", "")
# Maximum messages to retrieve per request
MAX_MESSAGES = int(os.environ.get("SLACK_MAX_MESSAGES", "100"))

# =============================================================================
# Server Setup
# =============================================================================

server = Server("slack-mcp")


def get_slack_client() -> WebClient:
    """Create a Slack WebClient with the configured bot token."""
    if not SLACK_BOT_TOKEN:
        raise ValueError(
            "SLACK_BOT_TOKEN environment variable is required. "
            "Create a Slack App and add the Bot Token."
        )
    return WebClient(token=SLACK_BOT_TOKEN)


def get_allowed_channels() -> set[str]:
    """Parse the channel allowlist from environment variable."""
    if not SLACK_CHANNEL_ALLOWLIST:
        return set()  # Empty set means all channels are allowed
    return {ch.strip() for ch in SLACK_CHANNEL_ALLOWLIST.split(",") if ch.strip()}


def is_channel_allowed(channel_id: str, channel_name: str) -> bool:
    """Check if a channel is in the allowlist (or if allowlist is empty)."""
    allowed = get_allowed_channels()
    if not allowed:
        return True  # No allowlist = all channels allowed
    return channel_id in allowed or channel_name in allowed


def format_timestamp(ts: str) -> str:
    """Convert Slack timestamp to human-readable format."""
    try:
        unix_ts = float(ts.split(".")[0])
        return datetime.fromtimestamp(unix_ts).strftime("%Y-%m-%d %H:%M:%S")
    except (ValueError, IndexError):
        return ts


# =============================================================================
# Tool Definitions
# =============================================================================

@server.list_tools()
async def list_tools() -> list[Tool]:
    """List available Slack tools."""
    return [
        Tool(
            name="slack_list_channels",
            description="""List accessible Slack channels.

Returns a list of channels the bot has access to. If a channel allowlist is
configured, only those channels will be returned.

Use this to discover available channels before reading or sending messages.""",
            inputSchema={
                "type": "object",
                "properties": {
                    "include_private": {
                        "type": "boolean",
                        "description": "Include private channels the bot is a member of (default: false)",
                        "default": False
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Maximum number of channels to return (default: 100)",
                        "default": 100
                    }
                }
            }
        ),
        Tool(
            name="slack_read_messages",
            description="""Read recent messages from a Slack channel.

Returns the most recent messages from the specified channel. Messages include
sender information, timestamp, and content.

Note: Only works for channels the bot has been added to and that are in the
allowlist (if configured).""",
            inputSchema={
                "type": "object",
                "properties": {
                    "channel": {
                        "type": "string",
                        "description": "Channel ID (e.g., 'C1234567890') or name (e.g., 'general')"
                    },
                    "limit": {
                        "type": "integer",
                        "description": f"Number of messages to retrieve (default: 20, max: {MAX_MESSAGES})",
                        "default": 20
                    }
                },
                "required": ["channel"]
            }
        ),
        Tool(
            name="slack_send_message",
            description="""Send a message to a Slack channel.

Posts a message to the specified channel. Supports basic Slack formatting
(bold, italic, links, etc.).

Note: Only works for channels the bot has been added to and that are in the
allowlist (if configured).

IMPORTANT: Use this tool responsibly. Messages are sent as the bot user.""",
            inputSchema={
                "type": "object",
                "properties": {
                    "channel": {
                        "type": "string",
                        "description": "Channel ID (e.g., 'C1234567890') or name (e.g., 'general')"
                    },
                    "message": {
                        "type": "string",
                        "description": "The message text to send (supports Slack formatting)"
                    },
                    "thread_ts": {
                        "type": "string",
                        "description": "Optional: Thread timestamp to reply in a thread"
                    }
                },
                "required": ["channel", "message"]
            }
        ),
        Tool(
            name="slack_delete_message",
            description="""Delete a message from a Slack channel.

Deletes a message using its timestamp. The bot can only delete messages it sent,
unless the bot has admin permissions.

Note: Use slack_read_messages to get message timestamps (ts field).""",
            inputSchema={
                "type": "object",
                "properties": {
                    "channel": {
                        "type": "string",
                        "description": "Channel ID (e.g., 'C1234567890') or name (e.g., 'general')"
                    },
                    "ts": {
                        "type": "string",
                        "description": "The timestamp of the message to delete (from the ts field)"
                    }
                },
                "required": ["channel", "ts"]
            }
        )
    ]


@server.call_tool()
async def call_tool(name: str, arguments: dict[str, Any]) -> list[TextContent]:
    """Handle tool calls."""
    try:
        if name == "slack_list_channels":
            return await handle_list_channels(arguments)
        elif name == "slack_read_messages":
            return await handle_read_messages(arguments)
        elif name == "slack_send_message":
            return await handle_send_message(arguments)
        elif name == "slack_delete_message":
            return await handle_delete_message(arguments)
        else:
            return [TextContent(type="text", text=f"Unknown tool: {name}")]
    except SlackApiError as e:
        error_msg = f"Slack API error: {e.response['error']}"
        if e.response.get("needed"):
            error_msg += f"\nMissing scope: {e.response['needed']}"
        return [TextContent(type="text", text=error_msg)]
    except Exception as e:
        error_msg = f"Error executing {name}: {str(e)}"
        return [TextContent(type="text", text=error_msg)]


async def handle_list_channels(arguments: dict[str, Any]) -> list[TextContent]:
    """List accessible Slack channels."""
    include_private = arguments.get("include_private", False)
    limit = min(arguments.get("limit", 100), 1000)

    client = get_slack_client()
    allowed = get_allowed_channels()

    # Get public channels
    types = "public_channel"
    if include_private:
        types += ",private_channel"

    # Fetch all channels with pagination
    channels = []
    cursor = None
    while True:
        result = client.conversations_list(
            types=types,
            limit=200,  # Fetch in batches of 200
            cursor=cursor,
            exclude_archived=True
        )

        for channel in result["channels"]:
            ch_id = channel["id"]
            ch_name = channel["name"]

            # Filter by allowlist if configured
            if allowed and not is_channel_allowed(ch_id, ch_name):
                continue

            channels.append({
                "id": ch_id,
                "name": ch_name,
                "is_private": channel.get("is_private", False),
                "is_member": channel.get("is_member", False),
                "num_members": channel.get("num_members", 0)
            })

            # Stop if we've reached the requested limit
            if len(channels) >= limit:
                break

        # Check for more pages
        cursor = result.get("response_metadata", {}).get("next_cursor")
        if not cursor or len(channels) >= limit:
            break

    if not channels:
        return [TextContent(type="text", text="No accessible channels found.")]

    output = "**Accessible Slack Channels**\n\n"
    output += "| ID | Name | Private | Bot Member | Members |\n"
    output += "|-----|------|---------|------------|--------|\n"

    for ch in channels:
        private_icon = "Yes" if ch["is_private"] else "No"
        member_icon = "Yes" if ch["is_member"] else "No"
        output += f"| {ch['id']} | #{ch['name']} | {private_icon} | {member_icon} | {ch['num_members']} |\n"

    if allowed:
        output += f"\n*Filtered by allowlist: {', '.join(allowed)}*"

    return [TextContent(type="text", text=output)]


async def handle_read_messages(arguments: dict[str, Any]) -> list[TextContent]:
    """Read messages from a Slack channel."""
    channel = arguments["channel"]
    limit = min(arguments.get("limit", 20), MAX_MESSAGES)

    client = get_slack_client()

    # Resolve channel name to ID if needed
    channel_id = await resolve_channel_id(client, channel)
    channel_info = await get_channel_info(client, channel_id)

    # Check allowlist
    if not is_channel_allowed(channel_id, channel_info.get("name", "")):
        return [TextContent(
            type="text",
            text=f"Error: Channel '{channel}' is not in the allowed channels list."
        )]

    # Get messages
    result = client.conversations_history(
        channel=channel_id,
        limit=limit
    )

    messages = result.get("messages", [])
    if not messages:
        return [TextContent(type="text", text=f"No messages found in #{channel_info.get('name', channel)}.")]

    # Get user info for display names
    user_cache = {}

    output = f"**Messages from #{channel_info.get('name', channel)}** ({len(messages)} messages)\n\n"

    # Messages are in reverse chronological order, reverse for natural reading
    for msg in reversed(messages):
        user_id = msg.get("user", "Unknown")

        # Cache user lookups
        if user_id not in user_cache and user_id != "Unknown":
            try:
                user_info = client.users_info(user=user_id)
                user_cache[user_id] = user_info["user"].get("real_name", user_info["user"].get("name", user_id))
            except SlackApiError:
                user_cache[user_id] = user_id

        username = user_cache.get(user_id, user_id)
        raw_ts = msg.get("ts", "")
        timestamp = format_timestamp(raw_ts)
        text = msg.get("text", "(no text)")

        # Handle bot messages
        if msg.get("bot_id"):
            username = msg.get("username", "Bot")

        output += f"**{username}** ({timestamp}) [ts: {raw_ts}]:\n{text}\n\n"

    return [TextContent(type="text", text=output)]


async def handle_send_message(arguments: dict[str, Any]) -> list[TextContent]:
    """Send a message to a Slack channel."""
    channel = arguments["channel"]
    message = arguments["message"]
    thread_ts = arguments.get("thread_ts")

    client = get_slack_client()

    # Resolve channel name to ID if needed
    channel_id = await resolve_channel_id(client, channel)
    channel_info = await get_channel_info(client, channel_id)

    # Check allowlist
    if not is_channel_allowed(channel_id, channel_info.get("name", "")):
        return [TextContent(
            type="text",
            text=f"Error: Channel '{channel}' is not in the allowed channels list."
        )]

    # Send message
    kwargs = {
        "channel": channel_id,
        "text": message
    }
    if thread_ts:
        kwargs["thread_ts"] = thread_ts

    result = client.chat_postMessage(**kwargs)

    output = f"**Message sent successfully**\n\n"
    output += f"- Channel: #{channel_info.get('name', channel)}\n"
    output += f"- Timestamp: {result['ts']}\n"
    if thread_ts:
        output += f"- Thread: {thread_ts}\n"
    output += f"- Message: {message[:100]}{'...' if len(message) > 100 else ''}"

    return [TextContent(type="text", text=output)]


async def handle_delete_message(arguments: dict[str, Any]) -> list[TextContent]:
    """Delete a message from a Slack channel."""
    channel = arguments["channel"]
    ts = arguments["ts"]

    client = get_slack_client()

    # Resolve channel name to ID if needed
    channel_id = await resolve_channel_id(client, channel)
    channel_info = await get_channel_info(client, channel_id)

    # Check allowlist
    if not is_channel_allowed(channel_id, channel_info.get("name", "")):
        return [TextContent(
            type="text",
            text=f"Error: Channel '{channel}' is not in the allowed channels list."
        )]

    # Delete message
    result = client.chat_delete(channel=channel_id, ts=ts)

    output = f"**Message deleted successfully**\n\n"
    output += f"- Channel: #{channel_info.get('name', channel)}\n"
    output += f"- Deleted timestamp: {ts}"

    return [TextContent(type="text", text=output)]


async def resolve_channel_id(client: WebClient, channel: str) -> str:
    """Resolve a channel name to its ID, or return the ID if already an ID."""
    # If it looks like an ID (starts with C, G, or D), return as-is
    if channel.startswith(("C", "G", "D")) and len(channel) >= 9:
        return channel

    # Remove # prefix if present
    channel_name = channel.lstrip("#")

    # Search for channel by name, handling pagination
    cursor = None
    while True:
        result = client.conversations_list(
            types="public_channel,private_channel",
            limit=200,
            cursor=cursor,
            exclude_archived=True
        )
        for ch in result["channels"]:
            if ch["name"] == channel_name:
                return ch["id"]

        # Check for more pages
        cursor = result.get("response_metadata", {}).get("next_cursor")
        if not cursor:
            break

    raise ValueError(f"Channel '{channel}' not found. Use channel ID or exact name.")


async def get_channel_info(client: WebClient, channel_id: str) -> dict:
    """Get information about a channel."""
    try:
        result = client.conversations_info(channel=channel_id)
        return result["channel"]
    except SlackApiError:
        return {"id": channel_id}


# =============================================================================
# Main Entry Point
# =============================================================================

async def main():
    """Run the MCP server."""
    async with stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            server.create_initialization_options()
        )


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())

#!/usr/bin/env python3
"""
Athena MCP Server

An MCP server that provides tools for querying AWS Athena tables.
Requires AWS SSO authentication: aws sso login --profile voodoo-adn-prod
"""

import json
import os
from typing import Any
from uuid import uuid4

import boto3
import awswrangler as wr
import pandas as pd
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent

# =============================================================================
# Configuration
# =============================================================================

AWS_PROFILE_NAME = os.environ.get("AWS_PROFILE_NAME", "voodoo-adn-prod")
AWS_REGION_NAME = os.environ.get("AWS_REGION_NAME", "eu-west-1")
WORKGROUP = os.environ.get("ATHENA_WORKGROUP", "adn-s3-query-engine")
DEFAULT_DATABASE = os.environ.get("ATHENA_DATABASE", "adn_lakehouse_silver")
S3_OUTPUT_BUCKET = os.environ.get(
    "ATHENA_S3_OUTPUT",
    "s3://voodoo-adn-lakehouse-sandbox-20240913130058669800000001/athena-mcp"
)

# =============================================================================
# Server Setup
# =============================================================================

server = Server("athena-mcp")


def get_boto3_session() -> boto3.Session:
    """Create a boto3 session with the configured AWS profile."""
    return boto3.Session(profile_name=AWS_PROFILE_NAME, region_name=AWS_REGION_NAME)


def dataframe_to_markdown(df: pd.DataFrame, max_rows: int = 100) -> str:
    """Convert a DataFrame to a markdown table string."""
    if len(df) > max_rows:
        df = df.head(max_rows)
        truncated = True
    else:
        truncated = False

    result = df.to_markdown(index=False)

    if truncated:
        result += f"\n\n*Results truncated. Showing {max_rows} of {len(df)} rows.*"

    return result


# =============================================================================
# Tool Definitions
# =============================================================================

@server.list_tools()
async def list_tools() -> list[Tool]:
    """List available Athena tools."""
    return [
        Tool(
            name="athena_query",
            description="""Execute a SQL query against AWS Athena.

Use this to query data from Athena tables. The query should be valid Presto/Trino SQL.
Results are returned as a markdown table.

Common tables:
- bid_pricer_log: Auction/bidding logs with timestamps, countries, apps, bid amounts
- Other tables available in adn_lakehouse_silver database

Tips:
- Always include appropriate WHERE clauses to limit data scanned
- Use LIMIT to restrict result set size
- server_timestamp is commonly used for time-based filtering""",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "The SQL query to execute"
                    },
                    "database": {
                        "type": "string",
                        "description": f"The Athena database to query (default: {DEFAULT_DATABASE})",
                        "default": DEFAULT_DATABASE
                    },
                    "max_rows": {
                        "type": "integer",
                        "description": "Maximum rows to return in output (default: 100)",
                        "default": 100
                    }
                },
                "required": ["query"]
            }
        ),
        Tool(
            name="athena_list_databases",
            description="List all available databases in Athena.",
            inputSchema={
                "type": "object",
                "properties": {}
            }
        ),
        Tool(
            name="athena_list_tables",
            description="List all tables in a specific Athena database.",
            inputSchema={
                "type": "object",
                "properties": {
                    "database": {
                        "type": "string",
                        "description": f"The database to list tables from (default: {DEFAULT_DATABASE})",
                        "default": DEFAULT_DATABASE
                    }
                }
            }
        ),
        Tool(
            name="athena_describe_table",
            description="Get the schema/structure of a specific Athena table.",
            inputSchema={
                "type": "object",
                "properties": {
                    "table": {
                        "type": "string",
                        "description": "The table name to describe"
                    },
                    "database": {
                        "type": "string",
                        "description": f"The database containing the table (default: {DEFAULT_DATABASE})",
                        "default": DEFAULT_DATABASE
                    }
                },
                "required": ["table"]
            }
        ),
        Tool(
            name="athena_sample_query",
            description="""Get sample data from bid_pricer_log table.

This is a convenience tool for quickly fetching auction log samples.
Returns bid data including timestamps, countries, apps, bid amounts, and win probability curves.""",
            inputSchema={
                "type": "object",
                "properties": {
                    "start_timestamp": {
                        "type": "string",
                        "description": "Start of time window in UTC (format: YYYY-MM-DD HH:MM:SS)"
                    },
                    "end_timestamp": {
                        "type": "string",
                        "description": "End of time window in UTC (format: YYYY-MM-DD HH:MM:SS)"
                    },
                    "country": {
                        "type": "string",
                        "description": "Optional: Filter by country code (e.g., 'US', 'FR')"
                    },
                    "app": {
                        "type": "string",
                        "description": "Optional: Filter by app name"
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Maximum number of records (default: 1000)",
                        "default": 1000
                    }
                },
                "required": ["start_timestamp", "end_timestamp"]
            }
        )
    ]


@server.call_tool()
async def call_tool(name: str, arguments: dict[str, Any]) -> list[TextContent]:
    """Handle tool calls."""
    try:
        if name == "athena_query":
            return await handle_athena_query(arguments)
        elif name == "athena_list_databases":
            return await handle_list_databases()
        elif name == "athena_list_tables":
            return await handle_list_tables(arguments)
        elif name == "athena_describe_table":
            return await handle_describe_table(arguments)
        elif name == "athena_sample_query":
            return await handle_sample_query(arguments)
        else:
            return [TextContent(type="text", text=f"Unknown tool: {name}")]
    except Exception as e:
        error_msg = f"Error executing {name}: {str(e)}"
        return [TextContent(type="text", text=error_msg)]


async def handle_athena_query(arguments: dict[str, Any]) -> list[TextContent]:
    """Execute a custom Athena query."""
    query = arguments["query"]
    database = arguments.get("database", DEFAULT_DATABASE)
    max_rows = arguments.get("max_rows", 100)

    session = get_boto3_session()

    df = wr.athena.read_sql_query(
        query,
        boto3_session=session,
        workgroup=WORKGROUP,
        database=database,
        ctas_approach=False,
        unload_approach=False,
        s3_output=f"{S3_OUTPUT_BUCKET}/{uuid4()}",
    )

    result = f"**Query Results** ({len(df)} rows)\n\n"
    result += dataframe_to_markdown(df, max_rows=max_rows)

    return [TextContent(type="text", text=result)]


async def handle_list_databases() -> list[TextContent]:
    """List available Athena databases."""
    session = get_boto3_session()

    databases = wr.catalog.databases(boto3_session=session)

    result = "**Available Databases**\n\n"
    for db in databases["Database"].tolist():
        result += f"- {db}\n"

    return [TextContent(type="text", text=result)]


async def handle_list_tables(arguments: dict[str, Any]) -> list[TextContent]:
    """List tables in a database."""
    database = arguments.get("database", DEFAULT_DATABASE)
    session = get_boto3_session()

    tables = wr.catalog.tables(database=database, boto3_session=session)

    result = f"**Tables in {database}**\n\n"
    if len(tables) == 0:
        result += "No tables found."
    else:
        for _, row in tables.iterrows():
            result += f"- {row['Table']}\n"

    return [TextContent(type="text", text=result)]


async def handle_describe_table(arguments: dict[str, Any]) -> list[TextContent]:
    """Describe a table's schema."""
    table = arguments["table"]
    database = arguments.get("database", DEFAULT_DATABASE)
    session = get_boto3_session()

    # Get table metadata
    columns = wr.catalog.table(database=database, table=table, boto3_session=session)

    result = f"**Schema for {database}.{table}**\n\n"
    result += "| Column | Type | Comment |\n"
    result += "|--------|------|--------|\n"

    for _, row in columns.iterrows():
        col_name = row.get("Column Name", row.get("Name", ""))
        col_type = row.get("Type", "")
        comment = row.get("Comment", "")
        result += f"| {col_name} | {col_type} | {comment} |\n"

    return [TextContent(type="text", text=result)]


async def handle_sample_query(arguments: dict[str, Any]) -> list[TextContent]:
    """Run a sample query on bid_pricer_log."""
    start_timestamp = arguments["start_timestamp"]
    end_timestamp = arguments["end_timestamp"]
    country = arguments.get("country")
    app = arguments.get("app")
    limit = arguments.get("limit", 1000)

    session = get_boto3_session()

    # Build query with optional filters
    where_clauses = [
        f"bpl.server_timestamp BETWEEN TIMESTAMP '{start_timestamp}' AND TIMESTAMP '{end_timestamp}'"
    ]

    if country:
        where_clauses.append(f"context.country = '{country}'")
    if app:
        where_clauses.append(f"context.app = '{app}'")

    where_clause = " AND ".join(where_clauses)

    query = f"""
        SELECT
            bid_id,
            CAST(bpl.server_timestamp AS TIMESTAMP) AS server_timestamp,
            context.country,
            context.app,
            mediation,
            JSON_FORMAT(CAST(win_proba_curve AS JSON)) AS win_proba_curve,
            response.bid,
            response.promoted_entity,
            optimizer.naive_base_reward AS reward
        FROM bid_pricer_log bpl
        WHERE {where_clause}
        AND win_proba_curve.bid_samples IS NOT NULL
        LIMIT {limit}
    """

    df = wr.athena.read_sql_query(
        query,
        boto3_session=session,
        workgroup=WORKGROUP,
        database=DEFAULT_DATABASE,
        ctas_approach=False,
        unload_approach=False,
        s3_output=f"{S3_OUTPUT_BUCKET}/{uuid4()}",
    )

    result = f"**Bid Pricer Log Sample** ({len(df)} rows)\n\n"
    result += f"Time range: {start_timestamp} to {end_timestamp}\n"
    if country:
        result += f"Country: {country}\n"
    if app:
        result += f"App: {app}\n"
    result += "\n"
    result += dataframe_to_markdown(df, max_rows=100)

    return [TextContent(type="text", text=result)]


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

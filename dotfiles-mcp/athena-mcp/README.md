# Athena MCP Server

An MCP (Model Context Protocol) server that enables Claude Code to query AWS Athena tables.

## Quick Start (Codespaces)

Run the setup script - it handles everything automatically:

```bash
cd mcp-servers/athena-mcp
./setup.sh
```

This will:
1. Install AWS CLI (if not present)
2. Configure the AWS SSO profile
3. Create Python virtual environment
4. Install dependencies
5. Create the `.mcp.json` config in the project root

Then authenticate with AWS SSO:

```bash
aws sso login --profile voodoo-adn-prod
```

Restart Claude Code and you're ready to go:

```bash
claude
```

## Manual Installation

If you prefer to set things up manually:

### Prerequisites

1. **AWS CLI** installed and configured
2. **Python 3.10+**
3. **AWS SSO** configured for the `voodoo-adn-prod` profile

### AWS SSO Configuration

Ensure your `~/.aws/config` includes:

```ini
[profile voodoo-adn-prod]
sso_start_url = https://voodoo-tech.awsapps.com/start
sso_account_id = 975049923261
sso_role_name = ADNAccessRO
region = eu-west-1
sso_region = eu-west-1
```

### Installation Steps

1. Create a virtual environment and install dependencies:

```bash
cd mcp-servers/athena-mcp
python -m venv venv
./venv/bin/pip install -r requirements.txt
```

2. Authenticate with AWS SSO:

```bash
aws sso login --profile voodoo-adn-prod
```

3. Start Claude Code from the repo root:

```bash
claude
```

No manual MCP configuration needed - the repo includes a `.mcp.json` file that Claude Code reads automatically.

## Available Tools

### 1. `athena_query`
Execute any SQL query against Athena.

```
Query: SELECT * FROM my_table WHERE date = '2024-01-01' LIMIT 10
```

### 2. `athena_list_databases`
List all available databases in your Athena catalog.

### 3. `athena_list_tables`
List all tables in a specific database.

### 4. `athena_describe_table`
Get the schema/structure of a table.

### 5. `athena_sample_query`
Convenience tool for querying `bid_pricer_log` with common filters:
- Time range (required)
- Country (optional)
- App (optional)

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `AWS_PROFILE_NAME` | `voodoo-adn-prod` | AWS profile to use |
| `AWS_REGION_NAME` | `eu-west-1` | AWS region |
| `ATHENA_WORKGROUP` | `adn-s3-query-engine` | Athena workgroup |
| `ATHENA_DATABASE` | `adn_lakehouse_silver` | Default database |
| `ATHENA_S3_OUTPUT` | (sandbox bucket) | S3 path for query results |

## Usage Examples

Once configured, you can ask Claude Code:

- "List all tables in the adn_lakehouse_silver database"
- "Describe the bid_pricer_log table schema"
- "Query the last 100 bids from France in the past hour"
- "Run this SQL: SELECT COUNT(*) FROM bid_pricer_log WHERE context.country = 'US'"

## Troubleshooting

### "ExpiredToken" or authentication errors
Run `aws sso login --profile voodoo-adn-prod` to refresh your credentials.

### "Database not found" errors
Check the database name and ensure you have access to it.

### Slow queries
- Add appropriate `WHERE` clauses to reduce data scanned
- Use `LIMIT` to restrict result set size
- Consider partitioned columns (like date) in filters

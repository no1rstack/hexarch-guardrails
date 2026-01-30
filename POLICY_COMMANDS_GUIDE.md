# Policy Commands Quick Reference

## Overview

The policy management suite provides commands for listing, exporting, validating, and comparing OPA (Open Policy Agent) policies in Hexarch.

## Quick Start

### List All Policies
```bash
hexarch-ctl policy list
```

**Output Formats**:
```bash
# Table format (default)
hexarch-ctl policy list --format table

# JSON format
hexarch-ctl policy list --format json

# CSV format
hexarch-ctl policy list --format csv
```

### Export a Policy
```bash
# Export single policy in Rego format
hexarch-ctl policy export ai_governance --format rego

# Export single policy in JSON format
hexarch-ctl policy export ai_governance --format json

# Export to file
hexarch-ctl policy export ai_governance -o policy.rego

# Export all policies
hexarch-ctl policy export --format json -o all_policies.json
```

### Validate a Policy
```bash
# Basic validation
hexarch-ctl policy validate ./policy.rego

# Strict validation
hexarch-ctl policy validate ./policy.rego --strict

# Check syntax without API
hexarch-ctl policy validate ./my_policy.rego
```

### Compare Policy Versions
```bash
# Show current version
hexarch-ctl policy diff ai_governance

# Compare specific versions
hexarch-ctl policy diff ai_governance --from 1.0.0 --to 1.1.0
```

## Command Reference

### `hexarch-ctl policy list`

List all OPA policies in the system.

**Options**:
- `--format {json|table|csv}` - Output format (default: table)
- `--filter PATTERN` - Filter policies by name or status
- `--limit N` - Limit results to N policies

**Example**:
```bash
hexarch-ctl policy list --format json
hexarch-ctl policy list --filter ai_governance
```

### `hexarch-ctl policy export`

Export OPA policy or all policies.

**Arguments**:
- `POLICY_NAME` - Name of policy to export (optional, exports all if omitted)

**Options**:
- `--format {rego|json}` - Export format (default: rego)
- `-o, --output FILE` - Output file path (default: stdout)
- `--include-metadata` - Include policy metadata

**Examples**:
```bash
# Export specific policy
hexarch-ctl policy export ai_governance

# Export all policies as JSON
hexarch-ctl policy export --format json

# Save to file
hexarch-ctl policy export ai_governance -o policies/ai_governance.rego
```

### `hexarch-ctl policy validate`

Validate OPA policy syntax offline.

**Arguments**:
- `POLICY_FILE` - Path to policy file to validate (required)

**Options**:
- `--strict` - Enable strict validation
- `--check-imports` - Verify all imports exist
- `--show-metrics` - Display rule count and metrics

**Examples**:
```bash
# Basic validation
hexarch-ctl policy validate ./policy.rego

# Strict mode
hexarch-ctl policy validate ./policy.rego --strict

# Show metrics
hexarch-ctl policy validate ./policy.rego --show-metrics
```

### `hexarch-ctl policy diff`

Compare policy versions.

**Arguments**:
- `POLICY_NAME` - Name of policy to compare (required)

**Options**:
- `--from VERSION` - Starting version (default: previous)
- `--to VERSION` - Ending version (default: current)
- `--format {text|unified|json}` - Diff format (default: text)
- `--color` - Colorize output (default: true)

**Examples**:
```bash
# Show current version
hexarch-ctl policy diff ai_governance

# Compare versions
hexarch-ctl policy diff ai_governance --from 1.0.0 --to 1.1.0

# JSON format
hexarch-ctl policy diff ai_governance --format json
```

## Common Workflows

### Backup All Policies

```bash
# Export all policies to JSON
hexarch-ctl policy export --format json -o backup_$(date +%Y%m%d).json

# Or as individual Rego files
mkdir -p policies_backup
for policy in $(hexarch-ctl policy list --format json | jq -r '.[].name'); do
  hexarch-ctl policy export "$policy" -o "policies_backup/$policy.rego"
done
```

### Validate Local Policy Before Upload

```bash
# Validate policy syntax
hexarch-ctl policy validate ./new_policy.rego --strict

# Check metrics
hexarch-ctl policy validate ./new_policy.rego --show-metrics
```

### Track Policy Changes

```bash
# View current policy version
hexarch-ctl policy diff ai_governance

# Compare with previous version
hexarch-ctl policy diff ai_governance --from 1.0.0

# Export as JSON for detailed comparison
hexarch-ctl policy diff ai_governance --format json
```

## Global Options

These options work with all policy commands:

```bash
# Use different configuration file
hexarch-ctl --config /etc/hexarch/config.yaml policy list

# Change output format globally
hexarch-ctl --format json policy list

# Override API URL
hexarch-ctl --api-url http://api.example.com policy list

# Use API token
hexarch-ctl --api-token "your-token" policy list
```

## Error Handling

### Connection Failed

**Error**: `Failed to fetch policies: Connection failed`

**Solutions**:
1. Verify API is running: `curl http://localhost:8080/api/policies`
2. Check API URL: `hexarch-ctl --api-url <correct-url> policy list`
3. Verify API token: `hexarch-ctl --api-token <token> policy list`

### File Not Found

**Error**: `Error: Path "<path>" does not exist.`

**Solution**:
- Verify file path: `ls -la <path>`
- Use absolute path: `hexarch-ctl policy validate /absolute/path/policy.rego`

### Invalid Rego Syntax

**Error**: `Policy validation failed: Invalid Rego syntax`

**Solution**:
- Check OPA syntax: `opa fmt -w policy.rego`
- Review OPA documentation: https://www.openpolicyagent.org/docs/latest/

## Output Examples

### Policy List - Table Format

```
Name               Status    Version  Updated           Rules
─────────────────────────────────────────────────────────────────
ai_governance      active    1.2.3    2026-01-29 12:00  15
data_classification active    1.0.0    2026-01-28 14:30  8
compliance         inactive  0.9.1    2026-01-15 09:00  12
```

### Policy List - JSON Format

```json
[
  {
    "name": "ai_governance",
    "status": "active",
    "version": "1.2.3",
    "updated": "2026-01-29T12:00:00Z",
    "rule_count": 15
  }
]
```

### Policy Validate - Success

```
✓ Policy validated successfully
  Package: ai_governance
  Rules: 15
  Warnings: 0
```

## Tips & Tricks

1. **Use JSON output for parsing**: `hexarch-ctl policy list --format json | jq '.[] | .name'`

2. **Export and backup policies regularly**:
   ```bash
   hexarch-ctl policy export --format json -o backup.json
   ```

3. **Validate before updating**: Always validate a policy locally before deploying

4. **Monitor changes**: Use `policy diff` to track changes between versions

5. **Pipe to other tools**: `hexarch-ctl policy export | tee policy.rego | wc -l`

## Troubleshooting

See [PHASE_2_POLICY_COMMANDS_COMPLETE.md](PHASE_2_POLICY_COMMANDS_COMPLETE.md) for detailed troubleshooting and integration information.

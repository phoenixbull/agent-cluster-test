---
name: automation-workflows
description: Create and manage automated workflows using cron, webhooks, and event triggers.
metadata: {"type":"automation","category":"workflows"}
---

# Automation Workflows

Build and manage automated workflows for OpenClaw.

## Features

- Cron-based scheduling
- Webhook triggers
- Event-driven automation
- Workflow orchestration

## Usage

Use for:
- Setting up automated tasks
- Creating workflow pipelines
- Integrating with external services
- Event-driven actions

## Examples

```bash
# Create cron job
openclaw cron add --name "Daily backup" --cron "0 2 * * *"

# Trigger webhook
curl -X POST https://your-webhook/trigger
```

## Common Workflows

- Daily backups
- Status reports
- Data synchronization
- Notification pipelines

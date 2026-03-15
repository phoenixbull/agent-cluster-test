---
name: auto-updater
description: Automatic updates for OpenClaw, skills, and dependencies with version management.
metadata: {"type":"maintenance","category":"system"}
---

# Auto Updater

Automatic update management for OpenClaw ecosystem.

## Features

- Version checking
- Automatic updates
- Rollback support
- Update notifications
- Dependency management

## Usage

Use for:
- Keeping OpenClaw up to date
- Updating skills automatically
- Managing dependencies
- Rollback bad updates

## Configuration

```json
{
  "autoUpdate": {
    "enabled": true,
    "schedule": "0 3 * * *",
    "notifyBefore": true,
    "autoRollback": true
  }
}
```

## Commands

```bash
# Check for updates
openclaw update check

# Update OpenClaw
openclaw update run

# Update skills
openclaw skills update
```

## Examples

- "Check for available updates"
- "Update to the latest version"
- "Rollback to previous version"

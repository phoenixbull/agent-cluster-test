---
name: skill-vetter
description: Validate, test, and quality-check OpenClaw skills before deployment.
metadata: {"type":"quality","category":"development"}
---

# Skill Vetter

Quality assurance and validation for OpenClaw skills.

## Features

- Skill validation
- Test execution
- Quality checks
- Documentation review

## Usage

Use when:
- Creating new skills
- Updating existing skills
- Before deploying skills to production
- Debugging skill issues

## Commands

```bash
# Validate skill
openclaw skills check <skill-name>

# Run skill tests
npx skill-test <skill-path>
```

## Checklist

- [ ] SKILL.md exists and is valid
- [ ] Scripts are executable
- [ ] Dependencies documented
- [ ] Tests pass
- [ ] Examples provided

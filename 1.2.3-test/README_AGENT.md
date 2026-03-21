# Bobby Axelrod Agent Stack

This folder is a standalone agent stack for Bobby Axelrod.

## Included context files
- AGENTS.md
- SOUL.md
- IDENTITY.md
- USER.md
- MEMORY.md
- HEARTBEAT.md
- TOOLS.md

## Interface intent
- User can talk to Bobby directly through a dedicated Telegram bot once wired locally.
- MAXIMUS may also coordinate Bobby by sending tasks into Bobby's isolated session.

## Current limitation
The current OpenClaw channel session cannot by itself create a new external Telegram chat identity. The stack is prepared locally; bot wiring must be done with a local runtime using the operator's bot token in `.env`.

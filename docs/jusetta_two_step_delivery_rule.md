# Jusetta Two-Step Delivery Rule

## Source
Operational instruction confirmed by Bobby Axe.

## Rule
Sending via Jusetta must be treated as two separate steps.

## Status
Confirmed working in practice on 2026-03-23:
- Step 1 via `sessions_send` produced `payload_ready`
- Step 2 via explicit Telegram delivery path reached the Boss in Telegram

### Step 1 — Orchestration / tasking
Use:
- `sessions_send(sessionKey="agent:jusetta:main", ...)`

Purpose:
- give Jusetta the task
- define the exact text / payload
- collect orchestration status such as `payload_ready`

This step is not the final Telegram delivery.

### Step 2 — External Telegram delivery
Use explicit outbound delivery path:
- `openclaw agent --agent jusetta --deliver --channel telegram --reply-account jusetta --reply-to 6964967907 --message "<text>"`

Purpose:
- actual outbound send to the Boss in Telegram

## Core separation
- `sessions_send` = orchestration
- `--deliver --channel telegram ...` = real external delivery

## Do not
- do not assume `sessions_send` itself is reliable final Telegram delivery
- do not ask Jusetta to speak as Bobby/Jack
- do not call the whole flow blocker if payload is already ready

## Correct logic
1. task set
2. payload ready
3. explicit external delivery
4. verify real delivery

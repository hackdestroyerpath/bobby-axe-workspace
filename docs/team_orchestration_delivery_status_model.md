# Team Orchestration vs External Delivery Status Model

## Purpose
Fix the working status model for team interaction so Jack does not mix:
1. task/payload status
2. external delivery confirmation status

This applies especially to agent-to-agent orchestration with Jusetta and external Telegram delivery to the Boss.

---

## Core separation
### A. Orchestration / task status
This answers:
- was the task received?
- was the payload understood?
- was the payload prepared?

### B. External delivery status
This answers:
- was the final outbound message/file actually confirmed as delivered to the Boss?

These are not the same thing.

---

## Operational rule
Do not treat missing external delivery confirmation as proof that the task itself failed.

If the agent:
- received the task
- understood it
- prepared the payload

then the task is not a blocker at the orchestration level.

The remaining issue is only delivery confirmation.

---

## Preferred status vocabulary
Use statuses like:
- `task_received`
- `payload_ready`
- `delivery_pending`
- `delivery_unknown`
- `delivery_confirmed`
- `delivery_failed`

Avoid calling the whole task a generic `blocker` when only the external delivery confirmation is unclear.

---

## Specific rule for Jusetta
### Internal handoff
- use `sessions_send` for orchestration/tasking
- treat statuses like `task_received` / `payload_ready` as orchestration-only

### External Telegram send to Boss
- use explicit delivery path
- do not rely on `sessions_send` confirm path as the canonical delivery proof
- canonical pattern:
  `openclaw agent --agent jusetta --deliver --channel telegram --reply-account jusetta --reply-to 6964967907 --message "<text>"`

### Confirmed working model
- Step 1: task through `agent:jusetta:main`
- Step 2: explicit outbound Telegram delivery
- success is determined by actual external delivery, not by internal `sessions_send` ack noise

---

## Jack rule
If Jusetta:
- got the task
- built the message/payload

but Telegram delivery was not confirmed through the unstable `sessions_send` confirmation layer,
Jack should classify this as:
- `payload_ready`
- `delivery_unknown` or `delivery_pending`

not as a full task `blocker`.

---

## Working principle
`sessions_send != final Telegram delivery`

It is acceptable for:
- orchestration
- task handoff
- payload coordination

It is not the canonical final proof of external user delivery.

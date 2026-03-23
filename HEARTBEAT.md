# HEARTBEAT.md — Bobby supervisory loop

On heartbeat:
1. Check whether Antares Capital has active unfinished tasks.
2. Check whether any assigned owner is stalled, drifting, or waiting without a valid reason.
3. Check whether any escalation to MAXIMUS is required.
4. Check whether current OpenClaw approach should be verified against docs.
5. Check whether local runtime signals require attention: gateway status, warnings, channels, sessions, memory readiness.
6. Check whether any upstream change should alter current assumptions: release, critical issue, regression, or docs clarification.
7. Check whether communication can be compressed into a clearer next action.
8. If there is no meaningful action, blocker, or quality issue, reply `HEARTBEAT_OK`.

Rules:
- heartbeat should be useful, not noisy
- prefer action over commentary
- do not spam Boss with passive internal chatter
- surface only meaningful management signals
- classify findings as Observe, Adapt, Intervene, or Escalate whenever possible

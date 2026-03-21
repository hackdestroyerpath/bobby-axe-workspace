# MICRO_STEPS.md

## Active chain

### TASK-BBY-010 — strategy refit
- [x] M1: translate voice-spec into code constraints
- [x] M2: reduce default grid levels toward 1..5
- [x] M3: add directional TP/SL fields to grid plan
- [x] M4: define neutral-grid removal rule

### TASK-BBY-008 — repeating loop runner
- [ ] M5: define loop input contract
- [ ] M6: implement repeat cycle shell/python loop
- [ ] M7: write loop status file
- [ ] M8: add safe stop condition

### TASK-BBY-002 — state/risk hardening
- [ ] M9: finalize invalidation -> clear grid state contract
- [ ] M10: finalize lock -> runner summary contract
- [ ] M11: add test for lock/invalidation state persistence

## Rule
After each completed micro-step:
1. mark it done here
2. update ACTION_LOG.md
3. update STATUS.md
4. continue immediately to the next open micro-step unless a real blocker exists

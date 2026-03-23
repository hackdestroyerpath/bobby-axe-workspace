# PLAYBOOK.md — Bobby management playbook

## 1. Task assignment template
- Task:
- Owner:
- Expected artifact:
- Priority:
- Checkpoint:
- Escalate if:

## 2. Status intake template
- Done:
- In progress:
- Blocked:
- Need from Bobby:

## 3. Upward report template
- What done:
- What active:
- What blocked:
- Recommended next move:

## 4. Anti-chaos intervention
When output is vague or stalled:
1. reduce the scope
2. redefine the artifact
3. set one owner
4. set a tighter checkpoint
5. escalate if this already failed before

## 5. Docs-first rule
Before important OpenClaw changes:
1. check local docs
2. check official docs
3. check source if needed
4. then decide

## 6. Best-method selection
Choose methods by:
1. correctness by docs
2. operational safety
3. maintainability
4. scalability
5. minimal chaos

## 7. Communication compression
Never push raw noise upward.
Always compress into:
- decision
- blocker
- recommendation
- next action

## 8. Team role routing
Default owner selection inside Antares Capital:
- Jack -> operational actions, integrations, quick technical tasks
- Ben_Kim -> analysis, validation, quality review
- Dollar_Bill -> forceful execution, follow-through, delivery pressure
- Jusetta -> user-facing communication, polished delivery, interface-sensitive messages
- Maffi -> implementation, assembly, operational handoff

If multiple agents are involved, Bobby must define:
1. first owner
2. handoff artifact
3. second owner
4. checkpoint
5. final reporting owner

## 9. OpenClaw report quality gate
Every meaningful OpenClaw report must answer:
- What was observed?
- What confirmed it?
- What does it mean?
- What is the risk?
- What is the next move?

Reject reports that rely on:
- guesswork without source
- decorative status without artifact
- long narration without decision value
- confusion between confirmed fact and hypothesis

## 10. Drift control
When an agent drifts:
1. narrow the task
2. redefine the artifact
3. shorten the checkpoint
4. require source-backed evidence
5. reassign if drift repeats

Drift indicators:
- vague language
- no artifact
- no docs/runtime/source validation
- unnecessary expansion of scope
- inability to separate executor error from environment error

## 11. Bobby update cadence
### Daily
- check `openclaw status`
- check warnings, channels, sessions, memory readiness
- scan upstream only if there is an active relevant theme or local instability
- produce a compressed digest only if action is needed

### Weekly
- review latest releases
- review key docs changes
- scan recurring issues/PR themes
- update internal operating rules if practice should change

### Event-driven
Trigger immediate verification when:
- runtime behavior is surprising
- docs and behavior diverge
- a new release touches our operating surface
- a recurring upstream bug maps to our local setup

## 12. Signal classification
End updates with one of:
- Observe
- Adapt
- Intervene
- Escalate

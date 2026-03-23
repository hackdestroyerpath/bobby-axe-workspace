# Ben_Kim Resolution Next Action

## Status
Phase 6 next-action note.

## Purpose
Коротко зафиксировать, какой practical implementation move теперь должен быть первым после всей materialization и resolution-definition работы.

---

# 1. Current position

At this point Ben_Kim already has:
- hardening tracks
- hardening notes
- closure criteria
- implementation order
- duplicate policy recommendation
- bridge from H1 into H2/H3

This means the next honest step is no longer more framing.
It is a first practical implementation-oriented move.

---

# 2. Recommended first move

## First practical move
Implement and validate the behavioral change:
- **duplicate = skip**

as an actual write-path behavior target.

---

# 3. Why this should be first

This is the highest-leverage move because it should improve three things at once:
1. replay safety
2. batch interpretation clarity
3. response accounting clarity

No other single change gives the same upstream effect right now.

---

# 4. Minimum acceptable first-change definition

The first real implementation-oriented progress should mean at least:
1. duplicate no longer appears as hard-failure class by default
2. duplicate no longer poisons the rest of batch interpretation
3. duplicate becomes explicitly visible as duplicate/skipped-like outcome

If these three are not true, progress is still mostly documentary rather than behavioral.

---

# 5. What should count as first real sign of progress

The first real sign of progress beyond documentation is:
- the system behaves differently on a replay scenario than it behaves today

Specifically:
- duplicate replay should no longer produce the same old failure pattern
- operator should be able to read duplicate outcome more safely

---

# 6. What should not be mistaken for progress

Do not mistake the following for real implementation progress:
- more notes of the same class
- better wording alone
- more summaries without runtime-behavior change
- stronger claims without changed replay outcome

---

# 7. Correct next action in one line

If only one next implementation-oriented step is taken, it should be:
- make duplicate replay resolve as `skip`, not as hard-failure poison.

---

# 8. Use

Этот note использовать как:
- current immediate-action marker;
- reminder of what counts as real progress after heavy materialization;
- bridge from documentation into actual hardening behavior change.

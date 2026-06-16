# Patch5 adoption review

Status: proposed stable methodology adoption.

Branch: adopt/github-connector-patch5-stable-20260615

This branch records adoption intent for GitHub Connector Patch5 stable final.

Evidence basis:

- TEST-009 PASS_STRONG: missing dispatch with content match becomes dirty observed-applied, not clean confirmation.
- TEST-010 PASS_STRONG: missing dispatch with content mismatch remains not observed and does not trigger recovery.
- TEST-011 PASS: stale SHA / 409 is an attempted-dispatch conflict.
- TEST-012 PASS_STRONG: stale secondary summaries cannot override primary request state.
- TEST-013 PASS_STRONG: low tool count alone is not connector-wide limited-read.
- TEST-014 PASS_STRONG: compact lifecycle/status/archive-gate dry run passed.

Adoption boundary:

- This branch does not execute the production agent task.
- This branch only installs the connector methodology entrypoint and review note.
- The exact stable package is retained in the control-plane artifact named github_connector_patch5_STABLE_FINAL_20260615T234337Z.zip.

Core operational rule:

Primary request state and append-only request log override stale summary mirrors. Clean applied status requires dispatch proof, response proof and readback proof.

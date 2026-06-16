# GitHub Connector short instruction Patch5

Status: Patch5 stable final v1.0.

Use Patch5 for all GitHub Connector work. The control-plane package is `github_connector_patch5_STABLE_FINAL_20260615T234337Z.zip` with SHA-256 `5498f741f2d2a2c5fe46625ed41202de79e9596c7690a6a4747bc4bb88f44d65`.

## Core rules

1. Append-only request log plus primary state and repository readback are authoritative.
2. Secondary mirrors such as pending files, open risks, changed paths, review manifests and final reports are summaries only.
3. Clean applied status requires dispatch proof, response proof and readback proof.
4. Missing dispatch with content match is dirty observed-applied, not clean confirmed.
5. Missing dispatch with content mismatch is not observed and must not trigger recovery with the same request.
6. Stale SHA or 409 conflict is an attempted-dispatch conflict, not not-sent.
7. Low tool count alone is not connector-wide limited-read unless the scan scope allows that inference.
8. Final handoff requires an archive consistency gate before the answer.

## Required state artifacts

- `01_connector_state.json`
- `02_connector_request_log.jsonl`
- `03_pending_writes.md`
- `04_surface_history.jsonl`
- `05_content_readback.jsonl`
- `open_risks.md`
- `changed_paths.md`
- `review_manifest.json`
- `FINAL_REPORT_FOR_VERIFIER.md`

See `github_connector_patch5/ADOPTION_REVIEW.md`.

# Jusetta Report Delivery Runbook

## Canonical delivery rule

All final reports for Boss must be sent to:
- **Email:** `Roslyy.nv@gmail.com`

## Sender identity rule

Every report email must clearly indicate that the report is from **Jusetta**.

Recommended subject format:
- `Report from Jusetta — <report name> — <timestamp>`

Recommended body header:
- `Report from Jusetta`
- `Generated at: <timestamp>`

## Timestamp rule

Every delivered report must include a clear report timestamp.

Minimum required timestamp fields:
- delivery timestamp
- report generation timestamp

Preferred timestamp format:
- ISO 8601 UTC
- Example: `2026-03-22T08:54:00Z`

## Current delivery channel

Primary delivery channel:
- **Email via SMTP**

Current sending mailbox:
- `koliahost999@mail.ru`

## Operational rule

When a report is ready, Jusetta should:
1. prepare the final report artifact
2. attach the report file
3. send it to `Roslyy.nv@gmail.com`
4. use a subject that includes `Jusetta` and a timestamp
5. ensure the message makes clear that the report is from Jusetta

## Notes

- Markdown remains the primary report authoring format.
- PDF may be used as an export/delivery artifact when required.
- GitHub is not the primary user delivery channel for final reports.

# New Data Collector — Step 7 Access Accounting Runtime

## Goal
Wire request accounting into the protected tick API.

This step adds runtime writes into:
- `collector_v2.api_access_log`

---

## What is logged
For `GET /ticks` requests, the system now logs at minimum:
- `client_id`
- `nickname`
- `endpoint`
- `symbol`
- `range_from_utc`
- `range_to_utc`
- `request_status`
- `row_count`
- `remote_addr`

---

## Logged cases
### Success
- valid key
- valid request
- rows returned
- `request_status = ok`

### Failure / rejection
- missing API key
- invalid/revoked key
- missing symbol
- invalid limit
- invalid datetime format

---

## Why this matters
This closes the gap between authentication and accountability.
The collector now not only restricts access, but also records who queried what and when.

---

## What still remains outside this step
- stats endpoint
- reporting/dashboard UI
- rate limiting
- admin interface

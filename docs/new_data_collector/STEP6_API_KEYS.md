# New Data Collector — Step 6 API Key Enforcement

## Goal
Turn the minimal read API into a protected API.

This step adds:
- API key validation in `GET /ticks`
- active/revoked client state enforcement
- helper runtime for issuing/revoking keys

This step does **not** yet add:
- per-request access accounting writes
- rate limits
- admin UI

---

## Files added/updated
- updated `new_collector/db.py`
- updated `new_collector/api.py`
- new `new_collector/clients.py`

---

## Behavior
### `GET /ticks`
Now requires header:
- `X-API-Key: <key>`

If key is missing:
- `401 missing_api_key`

If key is invalid or revoked:
- `401 invalid_or_revoked_api_key`

If key is valid and active:
- request is served
- response includes `client_id` and `nickname`

---

## Client registry runtime
### Issue / rotate key
```bash
python clients.py issue --client-id boss --nickname Boss
```

### Revoke key
```bash
python clients.py revoke --client-id boss
```

---

## Why this step matters
This is the first moment where the collector becomes an actual restricted substrate for downstream clients instead of an open local endpoint.

---

## Known limitations
- access log writes are not yet integrated into the runtime
- no per-client stats endpoint yet
- no admin UI yet

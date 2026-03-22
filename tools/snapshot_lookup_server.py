from __future__ import annotations

import argparse
import hashlib
import html
import json
import os
import sys
from datetime import UTC, datetime
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.snapshot_lookup_backend import SnapshotLookupBackend

LOOKUP_EXPORT_DIR = ROOT / 'tools' / 'snapshot_lookup_exports'
LOOKUP_EXPORT_DIR.mkdir(parents=True, exist_ok=True)


HTML_PAGE = """<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>Snapshot Lookup</title>
  <style>
    body { font-family: Arial, sans-serif; margin: 24px; background:#0b1020; color:#e8ecf3; }
    .wrap { max-width: 1200px; margin: 0 auto; }
    .card { background:#121933; border:1px solid #27315f; border-radius:12px; padding:16px; margin-bottom:16px; }
    .row { display:flex; gap:16px; flex-wrap:wrap; }
    .col { flex:1; min-width:280px; }
    input[type=text] { width:100%; padding:12px; border-radius:8px; border:1px solid #3a4a8a; background:#0f1530; color:#fff; }
    button { padding:12px 18px; border:none; border-radius:8px; background:#4f7cff; color:#fff; cursor:pointer; }
    button:hover { background:#658cff; }
    .grid { display:grid; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); gap:12px; }
    .metric { background:#0f1530; border:1px solid #27315f; border-radius:10px; padding:12px; }
    .label { color:#92a0c6; font-size:12px; text-transform:uppercase; }
    .value { font-size:16px; margin-top:6px; word-break:break-word; }
    .status-ready, .status-usable, .status-ok { color:#5ee38d; }
    .status-partial { color:#ffd166; }
    .status-blocked, .status-not_found, .status-error, .status-false { color:#ff6b6b; }
    .status-true { color:#5ee38d; }
    pre { white-space:pre-wrap; word-break:break-word; background:#0f1530; padding:12px; border-radius:8px; overflow:auto; }
    .hidden { display:none; }
  </style>
</head>
<body>
  <div class="wrap">
    <div class="card">
      <h1>Snapshot Lookup</h1>
      <p>Enter a <code>snapshot_id</code>. All dependent fields are resolved automatically.</p>
      <div class="row">
        <div class="col" style="flex:2; min-width:320px;">
          <input id="snapshotId" type="text" placeholder="snapshot_id / bundle_id / correlation_id" />
        </div>
        <div class="col" style="flex:1.3; min-width:260px;">
          <input id="apiKey" type="password" placeholder="API Key" />
        </div>
        <div class="col" style="flex:1; min-width:220px;">
          <select id="selectedSymbol" style="width:100%; padding:12px; border-radius:8px; border:1px solid #3a4a8a; background:#0f1530; color:#fff;">
            <option value="">optional symbol (choose from snapshot)</option>
          </select>
        </div>
        <div class="col" style="flex:0; min-width:160px;">
          <button id="refreshBtn">Refresh</button>
        </div>
      </div>
      <div class="row" style="margin-top:12px; align-items:center;">
        <label><input id="autoRefresh" type="checkbox" /> Auto-refresh every 7s</label>
        <span id="refreshState" style="color:#92a0c6; margin-left:12px;">Idle</span>
        <button id="downloadJsonBtn" style="margin-left:12px;">Download JSON</button>
        <button id="saveJsonBtn" style="margin-left:12px;">Save to Project</button>
      </div>
    </div>

    <div id="result" class="hidden">
      <div class="card">
        <h3>Operator Summary</h3>
        <div class="grid" id="summaryGrid"></div>
        <div style="margin-top:12px; color:#92a0c6;" id="scopeNote">Readiness scope note will appear here after lookup.</div>
      </div>
      <div class="row">
        <div class="col card">
          <h3>Snapshot Meta</h3>
          <div class="grid" id="metaGrid"></div>
        </div>
        <div class="col card">
          <h3>Readiness</h3>
          <div class="grid" id="readinessGrid"></div>
        </div>
        <div class="col card">
          <h3>Downstream</h3>
          <div class="grid" id="downstreamGrid"></div>
        </div>
      </div>
      <div class="card">
        <h3>Artifacts</h3>
        <pre id="artifactsPre"></pre>
      </div>
      <div class="card">
        <h3>Access Stats</h3>
        <div class="grid" id="statsSummaryGrid"></div>
        <div class="card" style="margin-top:12px; background:#0f1530;">
          <h4 style="margin-top:0;">By User</h4>
          <pre id="statsByUserPre"></pre>
        </div>
        <div class="card" style="margin-top:12px; background:#0f1530;">
          <h4 style="margin-top:0;">By Endpoint</h4>
          <pre id="statsByEndpointPre"></pre>
        </div>
        <div class="card" style="margin-top:12px; background:#0f1530;">
          <h4 style="margin-top:0;">By Status</h4>
          <pre id="statsByStatusPre"></pre>
        </div>
        <div class="card" style="margin-top:12px; background:#0f1530;">
          <h4 style="margin-top:0;">Recent Requests</h4>
          <pre id="statsRecentPre"></pre>
        </div>
      </div>
      <div class="card">
        <h3>Errors / Notes</h3>
        <pre id="notesPre"></pre>
      </div>
    </div>
  </div>

<script>
function metric(label, value, cls='') {
  return `<div class="metric"><div class="label">${label}</div><div class="value ${cls}">${value ?? '—'}</div></div>`;
}
function statusClass(v) {
  if (!v) return '';
  return 'status-' + String(v).replace(/[^a-zA-Z0-9_]/g, '_').toLowerCase();
}
let autoTimer = null;

function authHeaders() {
  const key = document.getElementById('apiKey').value.trim();
  const headers = {};
  if (key) headers['X-API-Key'] = key;
  return headers;
}

function persistApiKey() {
  try { localStorage.setItem('snapshotLookupApiKey', document.getElementById('apiKey').value); } catch {}
}

function loadApiKey() {
  try {
    const v = localStorage.getItem('snapshotLookupApiKey');
    if (v) document.getElementById('apiKey').value = v;
  } catch {}
}

async function lookup() {
  const id = document.getElementById('snapshotId').value.trim();
  const symbol = document.getElementById('selectedSymbol').value.trim();
  if (!id) return;
  document.getElementById('refreshState').textContent = 'Loading...';
  persistApiKey();
  const res = await fetch(`/lookup?snapshot_id=${encodeURIComponent(id)}&symbol=${encodeURIComponent(symbol)}`, { headers: authHeaders() });
  const data = await res.json();
  document.getElementById('result').classList.remove('hidden');

  const meta = data.snapshot || {};
  const downstream = data.downstream || {};
  const frames = (data.readiness || {}).frames || {};
  const symbols = meta.symbols || [];
  const symbolInput = document.getElementById('selectedSymbol');
  const currentSymbol = symbolInput.value;
  symbolInput.innerHTML = ['<option value="">optional symbol (choose from snapshot)</option>']
    .concat(symbols.map(x => `<option value="${String(x).replace(/"/g, '&quot;')}">${x}</option>`))
    .join('');
  if (meta.symbol && symbols.includes(meta.symbol)) {
    symbolInput.value = meta.symbol;
  } else if (currentSymbol && symbols.includes(currentSymbol)) {
    symbolInput.value = currentSymbol;
  }

  document.getElementById('summaryGrid').innerHTML = [
    metric('lookup', `${(data.lookup || {}).status || '—'} via ${(data.lookup || {}).resolved_by || '—'}`, statusClass((data.lookup || {}).status)),
    metric('symbol', meta.symbol || '—'),
    metric('symbol_count', String(meta.symbol_count ?? 0)),
    metric('as_of_utc', meta.as_of_utc || '—'),
    metric('production', meta.production_status || '—', statusClass(meta.production_status)),
    metric('Ben_Kim', String(downstream.usable_for_ben_kim), statusClass(String(downstream.usable_for_ben_kim))),
    metric('Jusetta', String(downstream.usable_for_jusetta), statusClass(String(downstream.usable_for_jusetta))),
    metric('Frame coverage', String((data.readiness || {}).full_frame_coverage), statusClass(String((data.readiness || {}).full_frame_coverage))),
  ].join('');

  document.getElementById('scopeNote').textContent = 'Frame readiness is resolved at or before snapshot as_of_utc.';

  document.getElementById('metaGrid').innerHTML = [
    metric('snapshot_id', meta.snapshot_id),
    metric('bundle_id', meta.bundle_id),
    metric('correlation_id', meta.correlation_id),
    metric('symbol', meta.symbol),
    metric('symbol_count', String(meta.symbol_count ?? 0)),
    metric('symbols', (meta.symbols || []).join(', ') || '—'),
    metric('as_of_utc', meta.as_of_utc),
    metric('production_status', meta.production_status, statusClass(meta.production_status)),
  ].join('');

  document.getElementById('readinessGrid').innerHTML = ['1m','5m','60m'].map(f => {
    const x = frames[f] || {};
    return metric(`${f} status`, `${x.status || 'missing'} | effective: ${x.observed_at || '—'}`, statusClass(x.status));
  }).join('');

  document.getElementById('downstreamGrid').innerHTML = [
    metric('Ben_Kim', String(downstream.usable_for_ben_kim), statusClass(String(downstream.usable_for_ben_kim))),
    metric('Jusetta', String(downstream.usable_for_jusetta), statusClass(String(downstream.usable_for_jusetta))),
    metric('Production', String(downstream.usable_for_production_analysis), statusClass(String(downstream.usable_for_production_analysis))),
    metric('Blocking reasons', (downstream.blocking_reasons || []).join(', ') || '—'),
  ].join('');

  document.getElementById('artifactsPre').textContent = JSON.stringify(data.artifacts || {}, null, 2);
  document.getElementById('notesPre').textContent = JSON.stringify({errors: data.errors || [], notes: data.notes || []}, null, 2);
  const statsRes = await fetch(`/stats?snapshot_id=${encodeURIComponent(id)}`, { headers: authHeaders() });
  const stats = await statsRes.json();
  const summary = stats.snapshot_summary || {};
  document.getElementById('statsSummaryGrid').innerHTML = [
    metric('Snapshot requests', String(summary.request_count ?? 0)),
    metric('Unique users', String(summary.unique_users ?? 0)),
    metric('Last request', summary.last_request_at || '—'),
  ].join('');
  document.getElementById('statsByUserPre').textContent = JSON.stringify((stats.by_user || []).map(x => ({
    nickname: x.nickname,
    total_requests: x.total_requests ?? x.request_count ?? 0,
    snapshot_requests: x.snapshot_requests ?? 0,
    last_request_at: x.last_request_at || null,
    snapshot_last_request_at: x.snapshot_last_request_at || null,
  })), null, 2);
  document.getElementById('statsByEndpointPre').textContent = JSON.stringify(stats.by_endpoint || [], null, 2);
  document.getElementById('statsByStatusPre').textContent = JSON.stringify(stats.by_status || [], null, 2);
  document.getElementById('statsRecentPre').textContent = JSON.stringify(stats.recent_requests || [], null, 2);
  document.getElementById('refreshState').textContent = 'Updated: ' + new Date().toLocaleTimeString();
}

function setAutoRefresh(enabled) {
  if (autoTimer) {
    clearInterval(autoTimer);
    autoTimer = null;
  }
  if (enabled) {
    autoTimer = setInterval(() => {
      const id = document.getElementById('snapshotId').value.trim();
      if (id) lookup();
    }, 7000);
    document.getElementById('refreshState').textContent = 'Auto-refresh enabled';
  }
}

document.getElementById('refreshBtn').addEventListener('click', lookup);
document.getElementById('downloadJsonBtn').addEventListener('click', () => {
  const id = document.getElementById('snapshotId').value.trim();
  const symbol = document.getElementById('selectedSymbol').value.trim();
  if (!id) return;
  document.getElementById('refreshState').textContent = 'Download endpoint requires API key via direct request; use Refresh/Save inside UI.';
});
document.getElementById('saveJsonBtn').addEventListener('click', async () => {
  const id = document.getElementById('snapshotId').value.trim();
  const symbol = document.getElementById('selectedSymbol').value.trim();
  if (!id) return;
  document.getElementById('refreshState').textContent = 'Saving...';
  persistApiKey();
  const res = await fetch(`/lookup/save?snapshot_id=${encodeURIComponent(id)}&symbol=${encodeURIComponent(symbol)}`, { headers: authHeaders() });
  const data = await res.json();
  document.getElementById('refreshState').textContent = data.saved_to ? `Saved: ${data.saved_to}` : 'Save failed';
});
document.getElementById('autoRefresh').addEventListener('change', (e) => setAutoRefresh(e.target.checked));
document.getElementById('apiKey').addEventListener('change', persistApiKey);
loadApiKey();
document.getElementById('snapshotId').addEventListener('keydown', (e) => {
  if (e.key === 'Enter') lookup();
});
</script>
</body>
</html>
"""


AUTH_OPTIONAL = os.environ.get('SNAPSHOT_LOOKUP_AUTH_OPTIONAL', '0') == '1'
ADMIN_API_KEY = os.environ.get('SNAPSHOT_LOOKUP_ADMIN_API_KEY', '').strip()


class SnapshotLookupHandler(BaseHTTPRequestHandler):
    backend = SnapshotLookupBackend()


    def do_POST(self) -> None:
        parsed = urlparse(self.path)
        client_ctx = self._authenticate()
        if parsed.path == '/analysis/write':
            if not client_ctx['allowed']:
                self._send_json({'error': 'unauthorized'}, status=HTTPStatus.UNAUTHORIZED)
                return
            length = int(self.headers.get('Content-Length', '0') or '0')
            raw = self.rfile.read(length)
            try:
                request_json = json.loads(raw.decode('utf-8'))
            except Exception:
                self._send_json({'error': 'invalid_json'}, status=HTTPStatus.BAD_REQUEST)
                return
            result = self.backend.write_analysis_results(request_json)
            self._log_access(client_ctx, request_json.get('snapshot_id'), None, request_json.get('snapshot_id'), 'analysis_write', result.get('status', 'ok'))
            self._send_json(result)
            return
        self._send_json({'error': 'not_found'}, status=HTTPStatus.NOT_FOUND)

    def do_GET(self) -> None:
        parsed = urlparse(self.path)
        client_ctx = self._authenticate()
        if parsed.path == '/health':
            self._send_json({'status': 'ok', 'auth_optional': AUTH_OPTIONAL, 'auth_mode': 'optional' if AUTH_OPTIONAL else 'mandatory'})
            return

        if parsed.path == '/payload':
            params = parse_qs(parsed.query)
            snapshot_id = (params.get('snapshot_id') or [''])[0].strip()
            selected_symbol = (params.get('symbol') or [''])[0].strip() or None
            if not snapshot_id:
                self._send_json({'error': 'snapshot_id is required'}, status=HTTPStatus.BAD_REQUEST)
                return
            if not client_ctx['allowed']:
                self._log_access(client_ctx, snapshot_id, selected_symbol, None, 'payload', 'denied')
                self._send_json({'error': 'unauthorized'}, status=HTTPStatus.UNAUTHORIZED)
                return
            result = self.backend.resolve_feature_payload(snapshot_id, selected_symbol=selected_symbol)
            self._log_access(client_ctx, snapshot_id, selected_symbol, result.get('bundle_id'), 'payload', result.get('result_code', 'ok'))
            self._send_json(result)
            return

        if parsed.path == '/strategies':
            params = parse_qs(parsed.query)
            agent = (params.get('agent') or ['Ben_Kim'])[0].strip() or 'Ben_Kim'
            if not client_ctx['allowed']:
                self._log_access(client_ctx, None, None, None, 'strategies', 'denied')
                self._send_json({'error': 'unauthorized'}, status=HTTPStatus.UNAUTHORIZED)
                return
            result = self.backend.get_strategy_registry(agent=agent)
            self._log_access(client_ctx, None, None, None, 'strategies', 'ok')
            self._send_json(result)
            return

        if parsed.path == '/lookup':
            params = parse_qs(parsed.query)
            snapshot_id = (params.get('snapshot_id') or [''])[0].strip()
            selected_symbol = (params.get('symbol') or [''])[0].strip() or None
            if not snapshot_id:
                self._send_json(
                    {
                        'error': 'snapshot_id is required',
                        'example': '/lookup?snapshot_id=<snapshot_id>',
                    },
                    status=HTTPStatus.BAD_REQUEST,
                )
                return
            if not client_ctx['allowed']:
                self._log_access(client_ctx, snapshot_id, selected_symbol, None, 'lookup', 'denied')
                self._send_json({'error': 'unauthorized'}, status=HTTPStatus.UNAUTHORIZED)
                return
            result = self.backend.resolve_snapshot(snapshot_id, selected_symbol=selected_symbol)
            self._log_access(client_ctx, snapshot_id, selected_symbol, result['snapshot'].get('bundle_id'), 'lookup', result['lookup'].get('status', 'ok'))
            self._send_json(result)
            return

        if parsed.path == '/lookup/download':
            params = parse_qs(parsed.query)
            snapshot_id = (params.get('snapshot_id') or [''])[0].strip()
            selected_symbol = (params.get('symbol') or [''])[0].strip() or None
            if not snapshot_id:
                self._send_json({'error': 'snapshot_id is required'}, status=HTTPStatus.BAD_REQUEST)
                return
            if not client_ctx['allowed']:
                self._log_access(client_ctx, snapshot_id, selected_symbol, None, 'lookup_download', 'denied')
                self._send_json({'error': 'unauthorized'}, status=HTTPStatus.UNAUTHORIZED)
                return
            result = self.backend.resolve_snapshot(snapshot_id, selected_symbol=selected_symbol)
            self._log_access(client_ctx, snapshot_id, selected_symbol, result['snapshot'].get('bundle_id'), 'lookup_download', result['lookup'].get('status', 'ok'))
            filename = f"snapshot_lookup_{snapshot_id.replace('/', '_')}.json"
            self._send_json(result, extra_headers={'Content-Disposition': f'attachment; filename="{filename}"'})
            return

        if parsed.path == '/lookup/save':
            params = parse_qs(parsed.query)
            snapshot_id = (params.get('snapshot_id') or [''])[0].strip()
            selected_symbol = (params.get('symbol') or [''])[0].strip() or None
            if not snapshot_id:
                self._send_json({'error': 'snapshot_id is required'}, status=HTTPStatus.BAD_REQUEST)
                return
            if not client_ctx['allowed']:
                self._log_access(client_ctx, snapshot_id, selected_symbol, None, 'lookup_save', 'denied')
                self._send_json({'error': 'unauthorized'}, status=HTTPStatus.UNAUTHORIZED)
                return
            result = self.backend.resolve_snapshot(snapshot_id, selected_symbol=selected_symbol)
            ts = datetime.now(UTC).strftime('%Y%m%dT%H%M%SZ')
            filename = f"snapshot_lookup_{snapshot_id.replace('/', '_')}_{ts}.json"
            out_path = LOOKUP_EXPORT_DIR / filename
            out_path.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding='utf-8')
            self._log_access(client_ctx, snapshot_id, selected_symbol, result['snapshot'].get('bundle_id'), 'lookup_save', 'saved')
            self._send_json({'status': 'saved', 'snapshot_id': snapshot_id, 'saved_to': str(out_path.relative_to(ROOT))})
            return

        if parsed.path == '/stats':
            params = parse_qs(parsed.query)
            snapshot_id = (params.get('snapshot_id') or [''])[0].strip() or None
            if not client_ctx['allowed']:
                self._log_access(client_ctx, snapshot_id, None, None, 'stats', 'denied')
                self._send_json({'error': 'unauthorized'}, status=HTTPStatus.UNAUTHORIZED)
                return
            self._log_access(client_ctx, snapshot_id, None, None, 'stats', 'ok')
            self._send_json(self.backend.get_access_stats(snapshot_id=snapshot_id))
            return

        if parsed.path == '/':
            self._log_access(client_ctx, None, None, None, 'ui_shell', 'ok' if client_ctx['allowed'] else 'anonymous')
            self._send_html(HTML_PAGE)
            return

        self._send_json(
            {
                'service': 'snapshot_lookup_server',
                'routes': {
                    'ui': '/',
                    'health': '/health',
                    'lookup': '/lookup?snapshot_id=<snapshot_id>',
                    'payload': '/payload?snapshot_id=<snapshot_id>&symbol=<symbol>',
                    'strategies': '/strategies?agent=Ben_Kim',
                    'analysis_write': 'POST /analysis/write',
                },
            },
            status=HTTPStatus.OK,
        )


    def _authenticate(self) -> dict:
        api_key = (self.headers.get('X-API-Key') or '').strip()
        if not api_key:
            if AUTH_OPTIONAL:
                return {'allowed': True, 'client_id': None, 'nickname': 'anonymous'}
            return {'allowed': False, 'client_id': None, 'nickname': 'anonymous'}

        key_hash = hashlib.sha256(api_key.encode('utf-8')).hexdigest()
        if ADMIN_API_KEY and api_key == ADMIN_API_KEY:
            return {'allowed': True, 'client_id': 'admin', 'nickname': 'admin'}

        with self.backend.db.connect() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT client_id, nickname, status
                    FROM collector.snapshot_api_clients
                    WHERE api_key_hash = %s
                    LIMIT 1
                    """,
                    (key_hash,),
                )
                row = cur.fetchone()
        if not row:
            return {'allowed': AUTH_OPTIONAL, 'client_id': None, 'nickname': 'anonymous'}
        if row['status'] != 'active':
            return {'allowed': False, 'client_id': row['client_id'], 'nickname': row['nickname']}
        return {'allowed': True, 'client_id': row['client_id'], 'nickname': row['nickname']}

    def _log_access(self, client_ctx: dict, snapshot_id: str | None, selected_symbol: str | None, resolved_bundle_id: str | None, endpoint: str, request_status: str) -> None:
        try:
            with self.backend.db.connect() as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        """
                        INSERT INTO collector.snapshot_access_log (
                            client_id, nickname, snapshot_id, selected_symbol, resolved_bundle_id, endpoint, request_status
                        ) VALUES (%s, %s, %s, %s, %s, %s, %s)
                        """,
                        (
                            client_ctx.get('client_id'),
                            client_ctx.get('nickname'),
                            snapshot_id,
                            selected_symbol,
                            resolved_bundle_id,
                            endpoint,
                            request_status,
                        ),
                    )
                conn.commit()
        except Exception:
            pass

    def log_message(self, format: str, *args) -> None:
        return

    def _send_json(self, payload, status: HTTPStatus = HTTPStatus.OK, extra_headers: dict | None = None) -> None:
        body = json.dumps(payload, ensure_ascii=False, indent=2).encode('utf-8')
        self.send_response(status)
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.send_header('Content-Length', str(len(body)))
        if extra_headers:
            for k, v in extra_headers.items():
                self.send_header(k, v)
        self.end_headers()
        self.wfile.write(body)

    def _send_html(self, html_content: str, status: HTTPStatus = HTTPStatus.OK) -> None:
        body = html_content.encode('utf-8')
        self.send_response(status)
        self.send_header('Content-Type', 'text/html; charset=utf-8')
        self.send_header('Content-Length', str(len(body)))
        self.end_headers()
        self.wfile.write(body)


def main() -> None:
    parser = argparse.ArgumentParser(description='HTTP server for snapshot lookup backend')
    parser.add_argument('--host', default='127.0.0.1')
    parser.add_argument('--port', type=int, default=8787)
    args = parser.parse_args()

    server = ThreadingHTTPServer((args.host, args.port), SnapshotLookupHandler)
    print(json.dumps({'host': args.host, 'port': args.port}, ensure_ascii=False))
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == '__main__':
    main()

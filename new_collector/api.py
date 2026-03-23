from __future__ import annotations

import argparse
import json
from datetime import datetime
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlparse

from config import load_settings
from db import DB


class TickAPIHandler(BaseHTTPRequestHandler):
    db: DB | None = None

    def do_GET(self) -> None:
        parsed = urlparse(self.path)
        if parsed.path == "/health":
            self._send_json({"status": "ok", "service": "data_collector_v2_api"})
            return

        if parsed.path == "/ticks":
            api_key = (self.headers.get("X-API-Key") or "").strip()
            remote_addr = self.client_address[0] if self.client_address else None
            if not api_key:
                assert self.db is not None
                self.db.log_api_access(None, None, "/ticks", None, None, None, "missing_api_key", None, remote_addr)
                self._send_json({"error": "missing_api_key"}, status=HTTPStatus.UNAUTHORIZED)
                return

            assert self.db is not None
            client = self.db.validate_api_key(api_key)
            if client is None:
                self.db.log_api_access(None, None, "/ticks", None, None, None, "invalid_or_revoked_api_key", None, remote_addr)
                self._send_json({"error": "invalid_or_revoked_api_key"}, status=HTTPStatus.UNAUTHORIZED)
                return

            params = parse_qs(parsed.query)
            symbol = (params.get("symbol") or [""])[0].strip().upper()
            range_from = (params.get("from") or [""])[0].strip()
            range_to = (params.get("to") or [""])[0].strip()
            limit_raw = (params.get("limit") or ["1000"])[0].strip() or "1000"

            if not symbol:
                self.db.log_api_access(client["client_id"], client["nickname"], "/ticks", None, None, None, "bad_request_missing_symbol", None, remote_addr)
                self._send_json({"error": "symbol is required"}, status=HTTPStatus.BAD_REQUEST)
                return

            try:
                limit = max(1, min(int(limit_raw), 10000))
            except ValueError:
                self.db.log_api_access(client["client_id"], client["nickname"], "/ticks", symbol, None, None, "bad_request_invalid_limit", None, remote_addr)
                self._send_json({"error": "invalid limit"}, status=HTTPStatus.BAD_REQUEST)
                return

            try:
                dt_from = datetime.fromisoformat(range_from) if range_from else None
                dt_to = datetime.fromisoformat(range_to) if range_to else None
            except ValueError:
                self.db.log_api_access(client["client_id"], client["nickname"], "/ticks", symbol, None, None, "bad_request_invalid_datetime", None, remote_addr)
                self._send_json({"error": "invalid datetime format; use ISO-8601"}, status=HTTPStatus.BAD_REQUEST)
                return

            rows = self.db.fetch_ticks(symbol, dt_from, dt_to, limit=limit)
            self.db.log_api_access(client["client_id"], client["nickname"], "/ticks", symbol, dt_from, dt_to, "ok", len(rows), remote_addr)
            self._send_json({
                "client_id": client["client_id"],
                "nickname": client["nickname"],
                "symbol": symbol,
                "count": len(rows),
                "rows": rows,
            })
            return

        self._send_json({"error": "not_found"}, status=HTTPStatus.NOT_FOUND)

    def _send_json(self, payload: dict, status: HTTPStatus = HTTPStatus.OK) -> None:
        body = json.dumps(payload, ensure_ascii=False, default=str).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


def run_api(host: str = "127.0.0.1", port: int = 8791) -> None:
    settings = load_settings()
    TickAPIHandler.db = DB(settings.database_url)
    server = ThreadingHTTPServer((host, port), TickAPIHandler)
    print(f"data_collector_v2 api listening on http://{host}:{port}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Data Collector v2 tick API")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8791)
    args = parser.parse_args()
    run_api(args.host, args.port)

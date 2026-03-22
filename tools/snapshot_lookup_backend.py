from __future__ import annotations

import json
import sys
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from collector.config import get_settings
from collector.db import Database


EXPORT_DIR = Path(__file__).resolve().parent.parent / 'collector' / 'exports'
RESOLVER_VERSION = 'v1'


def _frame_template() -> dict[str, Any]:
    return {
        'status': 'missing',
        'observed_at': None,
        'packet_status': None,
        'packet_result_code': None,
        'stale': None,
        'insufficient_history_flag': None,
    }


def _base_response(snapshot_id: str) -> dict[str, Any]:
    return {
        'request': {
            'snapshot_id': snapshot_id,
            'resolved_at_utc': datetime.now(UTC).isoformat().replace('+00:00', 'Z'),
            'resolver_version': RESOLVER_VERSION,
        },
        'lookup': {
            'status': 'not_found',
            'resolved_by': 'none',
            'found': False,
        },
        'snapshot': {
            'snapshot_id': snapshot_id,
            'bundle_id': None,
            'correlation_id': None,
            'symbol': None,
            'symbol_count': 0,
            'symbols': [],
            'as_of_utc': None,
            'handoff_status': None,
            'data_status': None,
            'feature_status': None,
            'production_status': 'not_found',
        },
        'readiness': {
            'frames': {
                '1m': _frame_template(),
                '5m': _frame_template(),
                '60m': _frame_template(),
            },
            'full_frame_coverage': False,
        },
        'downstream': {
            'usable_for_ben_kim': False,
            'usable_for_jusetta': False,
            'usable_for_production_analysis': False,
            'blocking_reasons': [],
        },
        'artifacts': {
            'json_export_ref': None,
            'dataset_refs': [],
            'source_tables': {
                'snapshot_bundle': 'collector.snapshot_bundle',
                'feature_packet': 'collector.feature_packet_tf',
                'second_bar': 'collector.second_bar',
                'raw_trades': 'collector.raw_trades',
            },
        },
        'errors': [],
        'notes': [],
    }


class SnapshotLookupBackend:
    def __init__(self, db: Database | None = None):
        self.db = db or Database(get_settings().database_url)

    def resolve_snapshot(self, snapshot_id: str, selected_symbol: str | None = None) -> dict[str, Any]:
        response = _base_response(snapshot_id)

        try:
            bundle_row, resolved_by = self._resolve_bundle(snapshot_id)
            if not bundle_row:
                response['errors'].append({
                    'code': 'SNAPSHOT_NOT_FOUND',
                    'message': 'No bundle or correlation match found for snapshot id.',
                    'context': {'snapshot_id': snapshot_id},
                })
                return response

            response['lookup'] = {
                'status': 'ok',
                'resolved_by': resolved_by,
                'found': True,
            }

            payload = bundle_row['payload_json'] or {}
            symbol, symbol_entry, symbols = self._resolve_symbol(payload, selected_symbol=selected_symbol)

            response['snapshot'].update({
                'bundle_id': bundle_row['bundle_id'],
                'correlation_id': bundle_row['correlation_id'],
                'symbol': symbol,
                'symbol_count': len(symbols),
                'symbols': symbols,
                'as_of_utc': self._iso(bundle_row['as_of_utc']),
                'handoff_status': bundle_row['handoff_status'],
                'data_status': bundle_row['data_status'],
                'feature_status': bundle_row['feature_status'],
                'production_status': 'partial',
            })

            if symbol is None:
                response['lookup']['status'] = 'partial'
                response['snapshot']['production_status'] = 'partial'
                response['errors'].append({
                    'code': 'SNAPSHOT_MULTI_SYMBOL_AMBIGUOUS',
                    'message': 'Snapshot resolves to multiple symbols; explicit symbol selection is required.',
                    'context': {'snapshot_id': snapshot_id, 'symbols': response['snapshot']['symbols']},
                })
                response['notes'].append(f"Snapshot resolved, but symbol is ambiguous because multiple symbols are present ({response['snapshot']['symbol_count']}).")
            else:
                readiness = self._fetch_frame_readiness(symbol, bundle_row['as_of_utc'])
                response['readiness']['frames'] = readiness
                response['readiness']['full_frame_coverage'] = all(v['status'] == 'ready' for v in readiness.values())

            self._attach_artifacts(response, bundle_row['bundle_id'], symbol_entry)
            self._derive_downstream(response)
            return response
        except Exception as exc:
            response['lookup']['status'] = 'error'
            response['snapshot']['production_status'] = 'blocked'
            response['errors'].append({
                'code': 'LOOKUP_ERROR',
                'message': str(exc),
                'context': {'snapshot_id': snapshot_id},
            })
            return response

    def _resolve_bundle(self, snapshot_id: str):
        with self.db.connect() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT
                        bundle_id,
                        correlation_id,
                        as_of_utc,
                        handoff_status,
                        data_status,
                        feature_status,
                        payload_json,
                        created_at_utc,
                        updated_at_utc
                    FROM collector.snapshot_bundle
                    WHERE bundle_id = %s OR correlation_id = %s
                    ORDER BY created_at_utc DESC
                    LIMIT 1
                    """,
                    (snapshot_id, snapshot_id),
                )
                row = cur.fetchone()
        if not row:
            return None, 'none'
        resolved_by = 'bundle_id' if row['bundle_id'] == snapshot_id else 'correlation_id'
        return row, resolved_by

    def _resolve_symbol(self, payload_json: dict[str, Any], selected_symbol: str | None = None):
        entries = payload_json.get('symbols') or []
        symbols = [x.get('symbol') for x in entries if x.get('symbol')]
        if selected_symbol:
            for entry in entries:
                if entry.get('symbol') == selected_symbol:
                    return selected_symbol, entry, symbols
            return None, None, symbols
        if len(entries) == 1:
            entry = entries[0]
            return entry.get('symbol'), entry, symbols
        if len(entries) == 0:
            return None, None, []
        return None, None, symbols

    def _fetch_frame_readiness(self, symbol: str, as_of_utc) -> dict[str, Any]:
        readiness = {'1m': _frame_template(), '5m': _frame_template(), '60m': _frame_template()}
        with self.db.connect() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    WITH ranked AS (
                        SELECT
                            symbol,
                            frame,
                            observed_at,
                            packet_status,
                            packet_result_code,
                            data_quality_status,
                            data_quality_result_code,
                            stale,
                            insufficient_history_flag,
                            row_number() OVER (
                                PARTITION BY symbol, frame
                                ORDER BY observed_at DESC
                            ) AS rn
                        FROM collector.feature_packet_tf
                        WHERE symbol = %s
                          AND frame IN ('1m', '5m', '60m')
                          AND observed_at <= %s
                          AND packet_status = 'ready'
                          AND packet_result_code = 'ok'
                          AND COALESCE(stale, false) = false
                          AND COALESCE(insufficient_history_flag, false) = false
                    )
                    SELECT symbol, frame, observed_at, packet_status, packet_result_code, stale, insufficient_history_flag
                    FROM ranked
                    WHERE rn = 1
                    """,
                    (symbol, as_of_utc),
                )
                rows = cur.fetchall()
        for row in rows:
            readiness[row['frame']] = {
                'status': 'ready',
                'observed_at': self._iso(row['observed_at']),
                'packet_status': row['packet_status'],
                'packet_result_code': row['packet_result_code'],
                'stale': row['stale'],
                'insufficient_history_flag': row['insufficient_history_flag'],
            }
        return readiness

    def _attach_artifacts(self, response: dict[str, Any], bundle_id: str, symbol_entry: dict[str, Any] | None) -> None:
        export_path = EXPORT_DIR / f'{bundle_id}.json'
        if export_path.exists():
            response['artifacts']['json_export_ref'] = str(export_path.relative_to(Path(__file__).resolve().parent.parent))
            response['artifacts']['dataset_refs'].append({
                'kind': 'snapshot_bundle',
                'ref': response['artifacts']['json_export_ref'],
            })
        if symbol_entry:
            for key in ('raw_ref', 'aggregate_ref', 'feature_ref'):
                if key in symbol_entry:
                    response['artifacts']['dataset_refs'].append({
                        'kind': key,
                        'ref': symbol_entry[key],
                    })

    def _derive_downstream(self, response: dict[str, Any]) -> None:
        if not response['lookup']['found']:
            response['snapshot']['production_status'] = 'not_found'
            response['downstream']['blocking_reasons'].append('snapshot_not_found')
            return

        if response['snapshot']['symbol'] is None:
            response['downstream']['blocking_reasons'].append('symbol_ambiguous')
            response['downstream']['usable_for_jusetta'] = True
            return

        full = response['readiness']['full_frame_coverage']
        response['downstream']['usable_for_ben_kim'] = full
        response['downstream']['usable_for_jusetta'] = full or bool(response['artifacts']['json_export_ref'])
        response['downstream']['usable_for_production_analysis'] = full

        if full:
            response['snapshot']['production_status'] = 'usable'
            response['notes'].append('Readiness derived with as_of_utc upper bound applied.')
        else:
            response['snapshot']['production_status'] = 'partial'
            response['downstream']['blocking_reasons'].append('frame_readiness_incomplete')
            response['notes'].append('At least one required frame is not ready at or before snapshot as_of_utc.')



    def resolve_feature_payload(self, snapshot_id: str, selected_symbol: str | None = None) -> dict[str, Any]:
        base = self.resolve_snapshot(snapshot_id, selected_symbol=selected_symbol)
        response = {
            'snapshot_id': base['snapshot']['snapshot_id'],
            'bundle_id': base['snapshot']['bundle_id'],
            'correlation_id': base['snapshot']['correlation_id'],
            'symbol': base['snapshot']['symbol'],
            'as_of_utc': base['snapshot']['as_of_utc'],
            'payload_status': 'blocked',
            'result_code': 'error',
            'frames': {
                '1m': {'status': 'missing', 'selected_by': 'best_observed_at_lte_as_of_utc', 'payload': None},
                '5m': {'status': 'missing', 'selected_by': 'best_observed_at_lte_as_of_utc', 'payload': None},
                '60m': {'status': 'missing', 'selected_by': 'best_observed_at_lte_as_of_utc', 'payload': None},
            },
            'notes': list(base.get('notes', [])),
        }

        if not base['lookup']['found']:
            response['payload_status'] = 'blocked'
            response['result_code'] = 'not_found'
            response['notes'].append('Snapshot not found for payload resolution.')
            return response

        if not base['snapshot']['symbol']:
            response['payload_status'] = 'blocked'
            response['result_code'] = 'error'
            response['notes'].append('Symbol resolution failed for payload endpoint.')
            return response

        rows = self._fetch_payload_rows(base['snapshot']['symbol'], base['snapshot']['as_of_utc'])
        ready_count = 0
        partial_count = 0
        for frame in ('1m', '5m', '60m'):
            row = rows.get(frame)
            if row is None:
                continue
            status = 'ready' if row['packet_status'] == 'ready' and row['packet_result_code'] == 'ok' else 'partial'
            if status == 'ready':
                ready_count += 1
            else:
                partial_count += 1
            response['frames'][frame] = {
                'status': status,
                'selected_by': 'best_observed_at_lte_as_of_utc',
                'payload': self._normalize_row(row),
            }

        if ready_count == 3:
            response['payload_status'] = 'ready'
            response['result_code'] = 'ok'
            response['notes'].append('All required frame payloads resolved at or before snapshot as_of_utc.')
        elif ready_count > 0 or partial_count > 0:
            response['payload_status'] = 'partial'
            response['result_code'] = 'partial'
            response['notes'].append('One or more frame payloads are partial or missing at snapshot as_of_utc.')
        else:
            response['payload_status'] = 'blocked'
            response['result_code'] = 'error'
            response['notes'].append('No frame payloads could be resolved for this snapshot and symbol.')

        return response

    def _fetch_payload_rows(self, symbol: str, as_of_utc: str | Any) -> dict[str, Any]:
        with self.db.connect() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    WITH ranked AS (
                        SELECT *,
                               row_number() OVER (
                                   PARTITION BY symbol, frame
                                   ORDER BY observed_at DESC
                               ) AS rn
                        FROM collector.feature_packet_tf
                        WHERE symbol = %s
                          AND frame IN ('1m', '5m', '60m')
                          AND observed_at <= %s
                    )
                    SELECT *
                    FROM ranked
                    WHERE rn = 1
                    """,
                    (symbol, as_of_utc),
                )
                rows = cur.fetchall()
        return {row['frame']: row for row in rows}

    def get_access_stats(self, snapshot_id: str | None = None) -> dict[str, Any]:
        with self.db.connect() as conn:
            with conn.cursor() as cur:
                if snapshot_id:
                    cur.execute(
                        """
                        WITH total_by_user AS (
                            SELECT COALESCE(nickname, 'anonymous') AS nickname,
                                   COUNT(*) AS total_requests,
                                   MAX(created_at_utc) AS last_request_at
                            FROM collector.snapshot_access_log
                            GROUP BY COALESCE(nickname, 'anonymous')
                        ),
                        snapshot_by_user AS (
                            SELECT COALESCE(nickname, 'anonymous') AS nickname,
                                   COUNT(*) AS snapshot_requests,
                                   MAX(created_at_utc) AS snapshot_last_request_at
                            FROM collector.snapshot_access_log
                            WHERE snapshot_id = %s
                            GROUP BY COALESCE(nickname, 'anonymous')
                        )
                        SELECT t.nickname,
                               t.total_requests,
                               t.last_request_at,
                               COALESCE(s.snapshot_requests, 0) AS snapshot_requests,
                               s.snapshot_last_request_at
                        FROM total_by_user t
                        LEFT JOIN snapshot_by_user s USING (nickname)
                        ORDER BY snapshot_requests DESC, total_requests DESC, nickname ASC
                        """,
                        (snapshot_id,),
                    )
                    by_user = cur.fetchall()

                    cur.execute(
                        """
                        SELECT snapshot_id,
                               COUNT(*) AS request_count,
                               COUNT(DISTINCT COALESCE(nickname, 'anonymous')) AS unique_users,
                               MAX(created_at_utc) AS last_request_at
                        FROM collector.snapshot_access_log
                        WHERE snapshot_id = %s
                        GROUP BY snapshot_id
                        """,
                        (snapshot_id,),
                    )
                    summary = cur.fetchone()
                else:
                    cur.execute(
                        """
                        SELECT COALESCE(nickname, 'anonymous') AS nickname,
                               COUNT(*) AS total_requests,
                               MAX(created_at_utc) AS last_request_at
                        FROM collector.snapshot_access_log
                        GROUP BY COALESCE(nickname, 'anonymous')
                        ORDER BY total_requests DESC, nickname ASC
                        LIMIT 20
                        """
                    )
                    by_user = cur.fetchall()
                    cur.execute(
                        """
                        SELECT snapshot_id,
                               COUNT(*) AS request_count,
                               COUNT(DISTINCT COALESCE(nickname, 'anonymous')) AS unique_users,
                               MAX(created_at_utc) AS last_request_at
                        FROM collector.snapshot_access_log
                        GROUP BY snapshot_id
                        ORDER BY request_count DESC, snapshot_id ASC
                        LIMIT 20
                        """
                    )
                    summary = None

                cur.execute(
                    """
                    SELECT COALESCE(nickname, 'anonymous') AS nickname,
                           snapshot_id,
                           endpoint,
                           request_status,
                           created_at_utc
                    FROM collector.snapshot_access_log
                    ORDER BY created_at_utc DESC
                    LIMIT 20
                    """
                )
                recent = cur.fetchall()

        return {
            'snapshot_summary': self._normalize_row(summary) if summary else None,
            'by_user': [self._normalize_row(x) for x in by_user],
            'recent_requests': [self._normalize_row(x) for x in recent],
        }

    def _normalize_row(self, row: Any) -> dict[str, Any] | None:
        if row is None:
            return None
        out = {}
        for k, v in dict(row).items():
            out[k] = self._normalize_value(v)
        return out

    @staticmethod
    def _iso(value: Any) -> str | None:
        if value is None:
            return None
        if hasattr(value, 'isoformat'):
            return value.isoformat().replace('+00:00', 'Z')
        return str(value)

    def _normalize_value(self, value: Any):
        if value is None:
            return None
        if isinstance(value, Decimal):
            return float(value)
        if hasattr(value, 'isoformat'):
            return self._iso(value)
        return value


if __name__ == '__main__':
    backend = SnapshotLookupBackend()
    sample = backend.resolve_snapshot('nonexistent')
    print(json.dumps(sample, ensure_ascii=False, indent=2))

from __future__ import annotations

import argparse
import json

from backfill import backfill_recent_ticks, maintain_continuity
from config import load_settings
from db import DB
from live import run_live_forever


def main() -> None:
    parser = argparse.ArgumentParser(description="Data Collector v2 baseline")
    parser.add_argument("mode", choices=["backfill", "live", "retention", "continuity"], help="run mode")
    args = parser.parse_args()

    settings = load_settings()
    db = DB(settings.database_url)

    if args.mode == "backfill":
        inserted = backfill_recent_ticks(settings, db)
        print(f"backfill_inserted={inserted}")
        return

    if args.mode == "retention":
        deleted = db.enforce_retention(settings.retention_days)
        print(f"retention_deleted={deleted}")
        return

    if args.mode == "continuity":
        result = maintain_continuity(settings, db)
        print(json.dumps(result, ensure_ascii=False, indent=2, default=str))
        return

    if args.mode == "live":
        run_live_forever(settings, db)
        return


if __name__ == "__main__":
    main()

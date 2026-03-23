from __future__ import annotations

import argparse

from config import load_settings
from db import DB


def main() -> None:
    parser = argparse.ArgumentParser(description="Data Collector v2 client registry runtime")
    sub = parser.add_subparsers(dest="command", required=True)

    issue = sub.add_parser("issue", help="issue or rotate an API key")
    issue.add_argument("--client-id", required=True)
    issue.add_argument("--nickname", required=True)
    issue.add_argument("--note", default="")

    revoke = sub.add_parser("revoke", help="revoke an API key")
    revoke.add_argument("--client-id", required=True)

    args = parser.parse_args()
    settings = load_settings()
    db = DB(settings.database_url)

    if args.command == "issue":
        api_key = db.issue_api_key(args.client_id, args.nickname, args.note or None)
        print(api_key)
        return

    if args.command == "revoke":
        affected = db.revoke_api_key(args.client_id)
        print(f"revoked={affected}")
        return


if __name__ == "__main__":
    main()

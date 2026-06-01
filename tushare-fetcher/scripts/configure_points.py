#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json

from tushare_runtime import load_user_points, save_user_points, user_config_path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Configure the user's Tushare points for tushare-fetcher")
    parser.add_argument("--points", type=int, help="Save the user's current Tushare points")
    parser.add_argument("--show", action="store_true", help="Show configured points")
    parser.add_argument("--config", help="Optional explicit config path")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if args.points is None and not args.show:
        args.show = True
    if args.points is not None:
        path = save_user_points(args.points, args.config)
        print(json.dumps({"status": "saved", "tushare_points": args.points, "config_path": str(path)}, ensure_ascii=False, indent=2))
        return 0
    points = load_user_points(args.config)
    print(json.dumps({"status": "found" if points is not None else "missing", "tushare_points": points, "config_path": str(user_config_path(args.config))}, ensure_ascii=False, indent=2))
    return 0 if points is not None else 3


if __name__ == "__main__":
    raise SystemExit(main())

"""Command-line interface for the IRIS QA gate.

Commands:
  qa init-db                 apply schema migrations + load fixtures (idempotent)
  qa run --dataset parcels   run one dataset's profile
  qa run --all               run every dataset
Options:
  --json DIR                 also write a JSON report per dataset (default: reports/)
  --no-db                    skip persisting to Postgres (JSON only)
  --quiet                    only print the one-line verdict per dataset

Exit code is 2 if any dataset BLOCKs (so the gate can fail a CI/promotion step),
0 otherwise (PASS or WARN both promote).
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from . import db
from .contracts import Outcome, RunResult
from .engine import run_profile
from .persist import persist_to_db, write_json_report
from .profiles import PROFILES, get_profile
from .report_html import write_html_report

REPO_ROOT = Path(__file__).resolve().parent.parent


def _run_sql_dir(conn, directory: Path) -> None:
    for path in sorted(directory.glob("*.sql")):
        db.run_script(conn, path.read_text(encoding="utf-8"))


def cmd_init_db(_: argparse.Namespace) -> int:
    with db.connect() as conn:
        _run_sql_dir(conn, REPO_ROOT / "db" / "migrations")
        _run_sql_dir(conn, REPO_ROOT / "db" / "fixtures")
    print("init-db: schema applied and fixtures loaded.")
    return 0


_ICON = {Outcome.PASS: "PASS ", Outcome.WARN: "WARN ", Outcome.BLOCK: "BLOCK"}


def _evidence_snippet(evidence: list[dict]) -> str:
    """A short human hint of what failed, for the terminal."""
    if not evidence:
        return ""
    first = evidence[0]
    key = first.get("key") or first.get("signature") or ""
    extras = [
        f"{k}={v}" for k, v in first.items()
        if k not in ("key", "signature") and v not in (None, "")
    ]
    tail = f" ({', '.join(extras)})" if extras else ""
    more = "" if len(evidence) <= 1 else f" +{len(evidence) - 1} more"
    return f"  e.g. {key}{tail}{more}"


def _print_verdict(result: RunResult, quiet: bool) -> None:
    gate = "promote" if result.promoted else "HELD"
    print(f"[{_ICON[result.overall]}] {result.dataset:<12} ({result.row_count} rows) -> {gate}")
    if quiet:
        return
    for c in result.checks:
        if c.outcome is Outcome.PASS:
            continue
        print(f"    {c.outcome.value:<5} {c.result.name:<24} {c.result.detail}"
              f"{_evidence_snippet(c.result.evidence)}")


def cmd_run(args: argparse.Namespace) -> int:
    datasets = list(PROFILES) if args.all else [args.dataset]
    if not datasets or datasets == [None]:
        print("error: pass --dataset <name> or --all", file=sys.stderr)
        return 1

    json_dir = Path(args.json) if args.json else REPO_ROOT / "reports"
    worst_rank = 0
    results = []
    with db.connect() as conn:
        for name in datasets:
            profile = get_profile(name)
            result = run_profile(conn, profile)
            run_id = None if args.no_db else persist_to_db(conn, result)
            write_json_report(result, json_dir / f"{name}_qa_report.json", run_id)
            _print_verdict(result, args.quiet)
            results.append(result)
            worst_rank = max(worst_rank, result.overall.rank)

    html_path = json_dir / "qa_report.html"
    write_html_report(results, html_path)
    print(f"\nHTML report: {html_path}")

    return 2 if worst_rank == Outcome.BLOCK.rank else 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="qa", description="IRIS dataset QA gate.")
    sub = parser.add_subparsers(dest="command", required=True)

    p_init = sub.add_parser("init-db", help="apply schema + load fixtures")
    p_init.set_defaults(func=cmd_init_db)

    p_run = sub.add_parser("run", help="run QA over one or all datasets")
    g = p_run.add_mutually_exclusive_group()
    g.add_argument("--dataset", choices=sorted(PROFILES), help="dataset to check")
    g.add_argument("--all", action="store_true", help="check every dataset")
    p_run.add_argument("--json", metavar="DIR", help="directory for JSON reports (default: reports/)")
    p_run.add_argument("--no-db", action="store_true", help="do not persist to Postgres")
    p_run.add_argument("--quiet", action="store_true", help="print only the per-dataset verdict")
    p_run.set_defaults(func=cmd_run)
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())

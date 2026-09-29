"""Render a QA run as a self-contained HTML dashboard.

No external libraries, no network — a single file the evaluator can open in any
browser. Shows every dataset, every check, the verdict, and the reason/evidence
for anything that failed.
"""

from __future__ import annotations

import html
from datetime import datetime

from .contracts import Outcome, RunResult

_BADGE = {
    Outcome.PASS: ("PASS", "#0f6e56", "#e1f5ee"),
    Outcome.WARN: ("WARN", "#854f0b", "#faeeda"),
    Outcome.BLOCK: ("BLOCK", "#a32d2d", "#fcebeb"),
}


def _badge(outcome: Outcome) -> str:
    label, fg, bg = _BADGE[outcome]
    return (
        f'<span style="background:{bg};color:{fg};padding:2px 10px;border-radius:999px;'
        f'font-size:12px;font-weight:600;letter-spacing:.02em">{label}</span>'
    )


def _evidence_text(evidence: list[dict]) -> str:
    """Turn a check's evidence rows into one short human-readable string."""
    if not evidence:
        return ""
    parts = []
    for item in evidence[:8]:
        key = item.get("key") or item.get("signature") or ""
        extras = [
            f"{k}={v}"
            for k, v in item.items()
            if k not in ("key", "signature") and v not in (None, "")
        ]
        joined = ", ".join(extras)
        parts.append(f"{key} ({joined})" if joined else str(key))
    more = "" if len(evidence) <= 8 else f" … +{len(evidence) - 8} more"
    return html.escape("; ".join(parts) + more)


def _dataset_card(result: RunResult) -> str:
    gate = "promote" if result.promoted else "HELD"
    gate_color = "#0f6e56" if result.promoted else "#a32d2d"
    rows = []
    for c in result.checks:
        reason = html.escape(c.result.detail)
        ev = _evidence_text(c.result.evidence)
        reason_cell = reason + (f'<div style="color:#6b6a63;margin-top:3px">{ev}</div>' if ev else "")
        rows.append(
            f"<tr>"
            f'<td style="padding:8px 12px;font-family:ui-monospace,monospace;font-size:13px">{html.escape(c.result.name)}</td>'
            f'<td style="padding:8px 12px;color:#6b6a63;font-size:13px">{html.escape(c.result.kind)}</td>'
            f'<td style="padding:8px 12px;font-size:13px">{html.escape(c.severity.value)}</td>'
            f'<td style="padding:8px 12px">{_badge(c.outcome)}</td>'
            f'<td style="padding:8px 12px;text-align:right;font-variant-numeric:tabular-nums">{c.result.failed_count}</td>'
            f'<td style="padding:8px 12px;font-size:13px">{reason_cell}</td>'
            f"</tr>"
        )
    return f"""
    <section style="border:1px solid #e4e2da;border-radius:12px;margin:18px 0;overflow:hidden">
      <header style="display:flex;align-items:center;gap:14px;padding:14px 18px;background:#faf9f5;border-bottom:1px solid #e4e2da">
        <h2 style="margin:0;font-size:18px;font-weight:600">{html.escape(result.dataset)}</h2>
        {_badge(result.overall)}
        <span style="color:#6b6a63;font-size:13px">{result.row_count} rows</span>
        <span style="margin-left:auto;color:{gate_color};font-weight:600;font-size:14px">{gate}</span>
      </header>
      <table style="width:100%;border-collapse:collapse">
        <thead>
          <tr style="text-align:left;color:#6b6a63;font-size:12px;text-transform:uppercase;letter-spacing:.04em">
            <th style="padding:8px 12px">Check</th><th style="padding:8px 12px">Type</th>
            <th style="padding:8px 12px">Severity</th><th style="padding:8px 12px">Outcome</th>
            <th style="padding:8px 12px;text-align:right">Failures</th><th style="padding:8px 12px">Reason / evidence</th>
          </tr>
        </thead>
        <tbody>{"".join(rows)}</tbody>
      </table>
    </section>"""


def render_html(results: list[RunResult], generated_at: datetime | None = None) -> str:
    generated_at = generated_at or datetime.now()
    blocked = sum(1 for r in results if r.overall is Outcome.BLOCK)
    warned = sum(1 for r in results if r.overall is Outcome.WARN)
    passed = sum(1 for r in results if r.overall is Outcome.PASS)
    summary = (
        f"{len(results)} datasets checked &middot; "
        f"<b style='color:#a32d2d'>{blocked} blocked</b>, "
        f"<b style='color:#854f0b'>{warned} warned</b>, "
        f"<b style='color:#0f6e56'>{passed} passed</b>"
    )
    cards = "".join(_dataset_card(r) for r in results)
    return f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>IRIS QA report</title></head>
<body style="margin:0;background:#f4f2ec;color:#2c2c2a;font-family:system-ui,-apple-system,'Segoe UI',sans-serif">
  <main style="max-width:960px;margin:0 auto;padding:32px 20px">
    <h1 style="font-size:24px;font-weight:600;margin:0 0 4px">IRIS dataset QA report</h1>
    <p style="color:#6b6a63;margin:0 0 2px">{summary}</p>
    <p style="color:#9c9a92;font-size:13px;margin:0 0 8px">generated {generated_at.strftime('%Y-%m-%d %H:%M')}</p>
    {cards}
    <footer style="color:#9c9a92;font-size:12px;margin-top:24px">
      A dataset promotes unless a BLOCK is present; WARN is visible but still promotes.
    </footer>
  </main>
</body></html>"""


def write_html_report(results: list[RunResult], path) -> None:
    from pathlib import Path

    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(render_html(results), encoding="utf-8")

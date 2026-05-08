"""
Module 4 — HTML Report Generator.

Produces a standalone, responsive HTML report with color-coded
mismatch rows, summary statistics, and modern styling.
"""

import logging
import os
from datetime import datetime
from string import Template
from typing import Any, Dict, List

from modules.mismatch_detector import compute_summary_statistics

logger = logging.getLogger(__name__)

# Using string.Template ($var) instead of str.format() to avoid
# conflicts with CSS curly braces.
HTML_TEMPLATE = Template("""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Audio-Subtitle Mismatch Report</title>
<style>
  :root {
    --bg: #f8fafc; --surface: #ffffff; --border: #e2e8f0;
    --text: #1e293b; --muted: #64748b;
    --green: #16a34a; --yellow: #ca8a04; --red: #dc2626;
    --accent: #2563eb;
  }
  * { margin:0; padding:0; box-sizing:border-box; }
  body {
    font-family: 'Segoe UI', system-ui, -apple-system, sans-serif;
    background: var(--bg); color: var(--text); line-height: 1.6;
    padding: 2rem; max-width: 1400px; margin: 0 auto;
  }
  h1 {
    font-size: 1.8rem; font-weight: 700;
    color: var(--text);
    margin-bottom: .25rem;
  }
  .subtitle { color: var(--muted); font-size: .9rem; margin-bottom: 2rem; }
  .summary-grid {
    display: grid; grid-template-columns: repeat(auto-fit, minmax(180px,1fr));
    gap: 1rem; margin-bottom: 2rem;
  }
  .card {
    background: var(--surface); border: 1px solid var(--border);
    border-radius: 6px; padding: 1.25rem; text-align: center;
  }
  .card .value { font-size: 2rem; font-weight: 700; }
  .card .label { font-size: .8rem; color: var(--muted); text-transform: uppercase; letter-spacing: .05em; }
  .card.match .value { color: var(--green); }
  .card.review .value { color: var(--yellow); }
  .card.missing .value { color: var(--red); }
  .card.score .value { color: var(--accent); }
  .table-wrap {
    overflow-x: auto; background: var(--surface);
    border: 1px solid var(--border); border-radius: 6px;
  }
  table { width: 100%; border-collapse: collapse; font-size: .9rem; }
  th {
    background: #f1f5f9; padding: .85rem 1rem; text-align: left;
    font-weight: 600; color: var(--muted); text-transform: uppercase;
    font-size: .75rem; letter-spacing: .05em; position: sticky; top: 0;
  }
  td { padding: .75rem 1rem; border-top: 1px solid var(--border); vertical-align: top; }
  tr:hover td { background-color: #f8fafc; }
  .status-badge {
    display: inline-block; padding: .2rem .65rem; border-radius: 4px;
    font-size: .75rem; font-weight: 600; text-transform: uppercase;
  }
  .badge-match   { background: #dcfce7; color: var(--green); }
  .badge-review  { background: #fef08a; color: var(--yellow); }
  .badge-missing { background: #fee2e2; color: var(--red); }
  .score-bar {
    width: 100%; height: 6px; background: var(--border); border-radius: 3px;
    overflow: hidden; margin-top: 4px;
  }
  .score-fill { height: 100%; border-radius: 3px; transition: width .3s; }
  
  /* Simplify: No full row background colors, just the reason column */
  td.reason-match { background-color: #e6ffe6 !important; }
  td.reason-review { background-color: #fffbeb !important; }
  td.reason-mismatch { background-color: #ffe6e6 !important; }
  
  footer {
    text-align: center; color: var(--muted); font-size: .8rem;
    margin-top: 2rem; padding-top: 1rem; border-top: 1px solid var(--border);
  }
  @media (max-width: 768px) {
    body { padding: 1rem; }
    .summary-grid { grid-template-columns: repeat(2,1fr); }
  }
</style>
</head>
<body>
<h1>Audio-Subtitle Mismatch Report</h1>
<p class="subtitle">Generated on $generated_at &mdash; $video_name</p>

<div class="summary-grid">
  <div class="card"><div class="value">$total</div><div class="label">Total Segments</div></div>
  <div class="card match"><div class="value">$match_count</div><div class="label">Matched ($match_pct%)</div></div>
  <div class="card review"><div class="value">$review_count</div><div class="label">Review ($review_pct%)</div></div>
  <div class="card missing"><div class="value">$missing_count</div><div class="label">Missing ($missing_pct%)</div></div>
  <div class="card score"><div class="value">$avg_score</div><div class="label">Avg Score</div></div>
</div>

<div class="table-wrap">
<table>
  <thead>
    <tr>
      <th>#</th><th>Timestamp</th><th>Audio Text</th>
      <th>Subtitle Text</th><th>Score</th><th>Status</th><th>Reason</th>
    </tr>
  </thead>
  <tbody>
$table_rows
  </tbody>
</table>
</div>

<footer>Lightweight Audio-Subtitle Mismatch Flagging Tool &copy; $year</footer>
</body>
</html>""")


def generate_report(
    results: List[Dict[str, Any]],
    output_path: str,
    video_name: str = "unknown",
) -> str:
    """
    Generate a standalone HTML report from mismatch results.

    Args:
        results:     List of mismatch result dicts.
        output_path: File path for the generated HTML.
        video_name:  Source video filename for the header.

    Returns:
        Absolute path to the generated report.
    """
    stats = compute_summary_statistics(results)
    rows_html = _build_table_rows(results)

    html = HTML_TEMPLATE.substitute(
        generated_at=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        video_name=video_name,
        total=stats.get("total_segments", 0),
        match_count=stats.get("match_count", 0),
        review_count=stats.get("review_count", 0),
        missing_count=stats.get("missing_count", 0),
        match_pct=stats.get("match_percentage", 0),
        review_pct=stats.get("review_percentage", 0),
        missing_pct=stats.get("missing_percentage", 0),
        avg_score=stats.get("average_score", 0),
        table_rows=rows_html,
        year=datetime.now().year,
    )

    os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as fh:
        fh.write(html)

    logger.info("HTML report generated → %s", output_path)
    return os.path.abspath(output_path)


def _build_table_rows(results: List[Dict[str, Any]]) -> str:
    rows = []
    for idx, r in enumerate(results, 1):
        status = r["status"]
        score = r["score"]
        reason = r.get("reason", "")

        if status == "MATCH":
            badge_class, bar_color = "badge-match", "var(--green)"
            reason_class = "reason-match"
        elif status == "REVIEW":
            badge_class, bar_color = "badge-review", "var(--yellow)"
            reason_class = "reason-review"
        else:
            badge_class, bar_color = "badge-missing", "var(--red)"
            reason_class = "reason-mismatch"

        sub_display = _escape(r["subtitle_text"]) if r["subtitle_text"] else "<em>&mdash;</em>"
        row = (
            f'    <tr>'
            f'<td>{idx}</td>'
            f'<td>{r.get("timestamp_display", str(r["timestamp"]))}</td>'
            f'<td>{_escape(r["audio_text"])}</td>'
            f'<td>{sub_display}</td>'
            f'<td>{score}'
            f'<div class="score-bar"><div class="score-fill" '
            f'style="width:{score}%;background:{bar_color};"></div></div></td>'
            f'<td><span class="status-badge {badge_class}">{status}</span></td>'
            f'<td class="{reason_class}">{reason}</td>'
            f'</tr>'
        )
        rows.append(row)
    return "\n".join(rows)


def _escape(text: str) -> str:
    """Basic HTML escaping."""
    return (
        text.replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
            .replace('"', "&quot;")
    )

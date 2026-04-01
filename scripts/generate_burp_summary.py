#!/usr/bin/env python3
import argparse
import html
import json
from pathlib import Path


def read_findings(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def render_list(items: list[str]) -> str:
    if not items:
        return "<li>None recorded</li>"
    return "".join(f"<li>{html.escape(item)}</li>" for item in items)


def render_findings(findings: list[dict]) -> str:
    if not findings:
        return (
            "<tr><td colspan=\"5\">No findings were recorded. "
            "Document manual review notes in notes.md.</td></tr>"
        )

    rows = []
    for finding in findings:
        rows.append(
            "<tr>"
            f"<td>{html.escape(finding.get('severity', 'info'))}</td>"
            f"<td>{html.escape(finding.get('title', 'Untitled finding'))}</td>"
            f"<td>{html.escape(finding.get('endpoint', 'n/a'))}</td>"
            f"<td>{html.escape(finding.get('details', ''))}</td>"
            f"<td>{html.escape(finding.get('evidence', ''))}</td>"
            "</tr>"
        )
    return "".join(rows)


def render_report(payload: dict) -> str:
    project = html.escape(payload.get("project", "spring-petclinic"))
    build_number = html.escape(str(payload.get("build_number", "manual")))
    tester = html.escape(payload.get("tester", "unassigned"))
    target_url = html.escape(payload.get("target_url", "http://petclinic-qa:8080/"))
    reviewed_at = html.escape(payload.get("reviewed_at", "not recorded"))
    decision = html.escape(payload.get("decision", "pass with notes"))
    summary = html.escape(payload.get("summary", "Manual Burp Community review completed."))

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>Burp Community Evidence Summary</title>
  <style>
    body {{
      font-family: Arial, sans-serif;
      margin: 2rem auto;
      max-width: 1100px;
      color: #12212f;
      line-height: 1.5;
      padding: 0 1rem;
    }}
    h1, h2 {{
      color: #083d77;
    }}
    .meta {{
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
      gap: 0.75rem;
      margin-bottom: 1.5rem;
    }}
    .card {{
      border: 1px solid #d7e3f0;
      border-radius: 10px;
      padding: 1rem;
      background: #f8fbff;
    }}
    .decision {{
      font-weight: bold;
    }}
    table {{
      width: 100%;
      border-collapse: collapse;
      margin-top: 1rem;
    }}
    th, td {{
      border: 1px solid #d7e3f0;
      padding: 0.75rem;
      vertical-align: top;
      text-align: left;
    }}
    th {{
      background: #edf5ff;
    }}
  </style>
</head>
<body>
  <h1>Burp Community Evidence Summary</h1>
  <div class="meta">
    <div class="card"><strong>Project</strong><br>{project}</div>
    <div class="card"><strong>Build</strong><br>{build_number}</div>
    <div class="card"><strong>Tester</strong><br>{tester}</div>
    <div class="card"><strong>Target URL</strong><br>{target_url}</div>
    <div class="card"><strong>Reviewed At</strong><br>{reviewed_at}</div>
    <div class="card"><strong>Decision</strong><br><span class="decision">{decision}</span></div>
  </div>

  <h2>Review Summary</h2>
  <p>{summary}</p>

  <h2>Endpoints Reviewed</h2>
  <ul>{render_list(payload.get("tested_paths", []))}</ul>

  <h2>Findings</h2>
  <table>
    <thead>
      <tr>
        <th>Severity</th>
        <th>Finding</th>
        <th>Endpoint</th>
        <th>Details</th>
        <th>Evidence</th>
      </tr>
    </thead>
    <tbody>{render_findings(payload.get("findings", []))}</tbody>
  </table>
</body>
</html>
"""


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate a Jenkins-publishable Burp Community HTML summary.")
    parser.add_argument("--input", required=True, help="Path to the JSON findings file.")
    parser.add_argument("--output", required=True, help="Path to write the HTML summary.")
    args = parser.parse_args()

    payload = read_findings(Path(args.input))
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(render_report(payload), encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

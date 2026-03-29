"""Report generation: JSON and Markdown outputs for eval runs."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from pathlib import Path


def build_report(
    *,
    run_id: str,
    api_url: str,
    start_time: datetime,
    results: list[dict[str, Any]],
) -> dict[str, Any]:
    """Build the structured report dict from raw results."""
    end_time = datetime.now(UTC)
    duration = (end_time - start_time).total_seconds()

    # Aggregate by category
    categories: dict[str, dict[str, Any]] = {}
    for r in results:
        cat = r["category"]
        if cat not in categories:
            categories[cat] = {"total": 0, "passed": 0, "failed": 0}
        categories[cat]["total"] += 1
        if r["verdict"] == "pass":
            categories[cat]["passed"] += 1
        else:
            categories[cat]["failed"] += 1

    for cat_data in categories.values():
        total = cat_data["total"]
        cat_data["pass_rate"] = round(cat_data["passed"] / total, 3) if total else 0.0

    total = len(results)
    passed = sum(1 for r in results if r["verdict"] == "pass")

    return {
        "run_id": run_id,
        "timestamp": end_time.isoformat(),
        "api_url": api_url,
        "duration_seconds": round(duration, 1),
        "summary": {
            "total": total,
            "passed": passed,
            "failed": total - passed,
            "pass_rate": round(passed / total, 3) if total else 0.0,
        },
        "categories": categories,
        "results": results,
    }


def save_json_report(report: dict[str, Any], output_dir: Path) -> Path:
    """Write the JSON report to output_dir/results.json."""
    output_dir.mkdir(parents=True, exist_ok=True)
    path = output_dir / "results.json"
    path.write_text(json.dumps(report, indent=2, ensure_ascii=False, default=str), encoding="utf-8")
    return path


def save_markdown_report(report: dict[str, Any], output_dir: Path) -> Path:
    """Write the Markdown report to output_dir/report.md."""
    output_dir.mkdir(parents=True, exist_ok=True)
    lines: list[str] = []

    lines.append(f"# Eval Run: {report['run_id']}")
    lines.append(
        f"**Fecha**: {report['timestamp']} | **API**: {report['api_url']} | **Duracion**: {report['duration_seconds']}s"
    )
    lines.append("")

    # Summary table
    lines.append("## Resumen")
    lines.append("| Categoria | Total | Pass | Fail | Rate |")
    lines.append("|-----------|-------|------|------|------|")
    for cat, data in report["categories"].items():
        rate_pct = f"{data['pass_rate'] * 100:.1f}%"
        lines.append(f"| {cat} | {data['total']} | {data['passed']} | {data['failed']} | {rate_pct} |")
    s = report["summary"]
    rate_pct = f"{s['pass_rate'] * 100:.1f}%"
    lines.append(f"| **TOTAL** | **{s['total']}** | **{s['passed']}** | **{s['failed']}** | **{rate_pct}** |")
    lines.append("")

    # Detail per category
    for cat in report["categories"]:
        cat_results = [r for r in report["results"] if r["category"] == cat]
        lines.append(f"## Detalle: {cat}")
        lines.append("| ID | Pregunta | Expected | Actual (truncado) | Veredicto |")
        lines.append("|----|----------|----------|--------------------|-----------|")
        for r in cat_results:
            question = _truncate(r.get("input", ""), 50)
            expected = _truncate(r.get("expected_output", r.get("expected_behavior", "")), 30)
            actual = _truncate(r.get("actual_output", ""), 40)
            verdict = "PASS" if r["verdict"] == "pass" else "FAIL"
            lines.append(f"| {r['id']} | {question} | {expected} | {actual} | {verdict} |")
        lines.append("")

    # Failures section
    failures = [r for r in report["results"] if r["verdict"] == "fail"]
    if failures:
        lines.append("## Failures")
        lines.append("| ID | Categoria | Razon del fallo |")
        lines.append("|----|-----------|----------------|")
        for r in failures:
            lines.append(f"| {r['id']} | {r['category']} | {r['reason']} |")
        lines.append("")

    path = output_dir / "report.md"
    path.write_text("\n".join(lines), encoding="utf-8")
    return path


def _truncate(text: str | None, max_len: int) -> str:
    """Truncate text for Markdown table cells."""
    if text is None:
        return ""
    text = text.replace("|", "\\|").replace("\n", " ")
    if len(text) <= max_len:
        return text
    return text[: max_len - 3] + "..."

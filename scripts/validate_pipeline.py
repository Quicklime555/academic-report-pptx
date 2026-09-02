#!/usr/bin/env python3
"""Validate evidence → outline → manuscript beats → slide mappings."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any


ID_PATTERNS = {
    "evidence": re.compile(r"^E\d{3,}$"),
    "outline": re.compile(r"^O\d{2,}$"),
    "beats": re.compile(r"^B\d{3,}$"),
    "slides": re.compile(r"^S\d{3,}$"),
}
BEAT_TYPES = {"content", "opening", "transition", "closing"}
PRIORITIES = {"core", "support", "optional", "backup"}
NON_CONTENT_ROLES = {"cover", "agenda", "section", "references", "closing"}


def problem(code: str, message: str, **extra: Any) -> dict[str, Any]:
    return {"code": code, "message": message, **extra}


def load_spec(path: Path) -> dict[str, Any]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise ValueError(f"Spec not found: {path}") from exc
    except json.JSONDecodeError as exc:
        raise ValueError(f"Invalid JSON: {exc}") from exc
    if not isinstance(data, dict):
        raise ValueError("Spec root must be an object.")
    return data


def require_text(item: dict[str, Any], field: str, errors: list[dict[str, Any]], owner: str) -> str:
    value = item.get(field)
    if not isinstance(value, str) or not value.strip():
        errors.append(problem("missing_text", f"{owner}.{field} must be non-empty."))
        return ""
    return value.strip()


def require_seconds(item: dict[str, Any], errors: list[dict[str, Any]], owner: str) -> float:
    value = item.get("estimated_seconds")
    if not isinstance(value, (int, float)) or value <= 0:
        errors.append(problem("invalid_seconds", f"{owner}.estimated_seconds must be positive."))
        return 0
    return float(value)


def collect_items(
    data: dict[str, Any],
    field: str,
    errors: list[dict[str, Any]],
) -> tuple[list[dict[str, Any]], dict[str, dict[str, Any]]]:
    raw = data.get(field)
    if not isinstance(raw, list):
        errors.append(problem("missing_array", f"{field} must be an array."))
        return [], {}
    items: list[dict[str, Any]] = []
    by_id: dict[str, dict[str, Any]] = {}
    pattern = ID_PATTERNS[field]
    for index, value in enumerate(raw):
        owner = f"{field}[{index}]"
        if not isinstance(value, dict):
            errors.append(problem("invalid_item", f"{owner} must be an object."))
            continue
        item_id = value.get("id")
        if not isinstance(item_id, str) or not pattern.match(item_id):
            errors.append(problem("invalid_id", f"{owner}.id has the wrong format: {item_id!r}"))
            continue
        if item_id in by_id:
            errors.append(problem("duplicate_id", f"Duplicate {field} id: {item_id}"))
            continue
        items.append(value)
        by_id[item_id] = value
    return items, by_id


def check_refs(
    raw_refs: Any,
    known: set[str],
    field: str,
    owner: str,
    errors: list[dict[str, Any]],
) -> list[str]:
    if not isinstance(raw_refs, list):
        errors.append(problem("invalid_refs", f"{owner}.{field} must be an array."))
        return []
    refs: list[str] = []
    for ref in raw_refs:
        if not isinstance(ref, str):
            errors.append(problem("invalid_ref", f"{owner}.{field} contains a non-string reference."))
            continue
        refs.append(ref)
        if ref not in known:
            errors.append(problem("dangling_ref", f"{owner}.{field} references missing id {ref}."))
    if len(refs) != len(set(refs)):
        errors.append(problem("duplicate_ref", f"{owner}.{field} contains duplicate references."))
    return refs


def speaking_budget(data: dict[str, Any], errors: list[dict[str, Any]]) -> float:
    duration = data.get("duration_minutes")
    qa = data.get("qa_minutes", 0)
    if not isinstance(duration, (int, float)) or duration <= 0:
        errors.append(problem("invalid_duration", "duration_minutes must be positive."))
        return 0
    if not isinstance(qa, (int, float)) or qa < 0 or qa >= duration:
        errors.append(problem("invalid_qa", "qa_minutes must be non-negative and shorter than duration_minutes."))
        return 0
    return float(duration - qa) * 60


def validate_pipeline(data: dict[str, Any], stage: str) -> dict[str, Any]:
    errors: list[dict[str, Any]] = []
    warnings: list[dict[str, Any]] = []
    budget = speaking_budget(data, errors)

    if data.get("version") != 2:
        errors.append(problem("version", "version must be 2."))
    for field in ("scenario", "stance", "language"):
        require_text(data, field, errors, "root")

    evidence, evidence_by_id = collect_items(data, "evidence", errors)
    outline, outline_by_id = collect_items(data, "outline", errors)
    if not evidence:
        errors.append(problem("evidence_empty", "At least one evidence item is required."))
    if not outline:
        errors.append(problem("outline_empty", "At least one outline section is required."))

    evidence_ids = set(evidence_by_id)
    outline_ids = set(outline_by_id)
    for item in evidence:
        owner = item["id"]
        require_text(item, "kind", errors, owner)
        require_text(item, "source", errors, owner)
        require_text(item, "claim", errors, owner)
    outline_seconds = 0.0
    for item in outline:
        owner = item["id"]
        require_text(item, "title", errors, owner)
        require_text(item, "purpose", errors, owner)
        outline_seconds += require_seconds(item, errors, owner)
        check_refs(item.get("evidence_refs", []), evidence_ids, "evidence_refs", owner, errors)
    if budget and outline_seconds > budget:
        errors.append(problem("outline_overrun", f"Outline budgets {outline_seconds:.0f}s but only {budget:.0f}s are available."))

    beats: list[dict[str, Any]] = []
    beats_by_id: dict[str, dict[str, Any]] = {}
    beat_seconds = 0.0
    if stage in {"manuscript", "slides"}:
        beats, beats_by_id = collect_items(data, "beats", errors)
        if not beats:
            errors.append(problem("beats_empty", "At least one manuscript beat is required."))
        used_outline: set[str] = set()
        for item in beats:
            owner = item["id"]
            outline_id = item.get("outline_id")
            if outline_id not in outline_ids:
                errors.append(problem("dangling_outline", f"{owner}.outline_id references missing id {outline_id!r}."))
            else:
                used_outline.add(str(outline_id))
            beat_type = item.get("type")
            if beat_type not in BEAT_TYPES:
                errors.append(problem("beat_type", f"{owner}.type must be one of {sorted(BEAT_TYPES)}."))
            priority = item.get("priority")
            if priority not in PRIORITIES:
                errors.append(problem("priority", f"{owner}.priority must be one of {sorted(PRIORITIES)}."))
            require_text(item, "title", errors, owner)
            require_text(item, "purpose", errors, owner)
            require_text(item, "spoken_text", errors, owner)
            beat_seconds += require_seconds(item, errors, owner)
            refs = check_refs(item.get("evidence_refs", []), evidence_ids, "evidence_refs", owner, errors)
            if beat_type == "content" and not refs:
                errors.append(problem("ungrounded_beat", f"Content beat {owner} must reference evidence."))
        for outline_id in sorted(outline_ids - used_outline):
            errors.append(problem("outline_unwritten", f"Outline section {outline_id} has no manuscript beat."))
        if budget and beat_seconds > budget:
            errors.append(problem("manuscript_overrun", f"Manuscript budgets {beat_seconds:.0f}s but only {budget:.0f}s are available."))

    slides: list[dict[str, Any]] = []
    core_coverage = 0.0
    if stage == "slides":
        slides, _ = collect_items(data, "slides", errors)
        expected_count = data.get("expected_slide_count")
        if not isinstance(expected_count, int) or expected_count <= 0:
            errors.append(problem("expected_slide_count", "expected_slide_count must be a positive integer."))
        elif expected_count != len(slides):
            errors.append(problem("slide_count", f"Expected {expected_count} slides, found {len(slides)}."))

        numbers: list[int] = []
        covered_beats: set[str] = set()
        beat_ids = set(beats_by_id)
        for item in slides:
            owner = item["id"]
            number = item.get("number")
            if not isinstance(number, int) or number <= 0:
                errors.append(problem("slide_number", f"{owner}.number must be a positive integer."))
            else:
                numbers.append(number)
            role = require_text(item, "role", errors, owner)
            require_text(item, "title", errors, owner)
            require_text(item, "template_layout", errors, owner)
            require_seconds(item, errors, owner)
            section_id = item.get("section_id")
            if section_id is not None and section_id not in outline_ids:
                errors.append(problem("slide_section", f"{owner}.section_id references missing id {section_id!r}."))
            beat_refs = check_refs(item.get("beat_refs", []), beat_ids, "beat_refs", owner, errors)
            evidence_refs = check_refs(item.get("evidence_refs", []), evidence_ids, "evidence_refs", owner, errors)
            if role not in NON_CONTENT_ROLES and not beat_refs:
                errors.append(problem("unmapped_slide", f"Academic content slide {owner} has no manuscript beat."))
            covered_beats.update(beat_refs)
            required_evidence: set[str] = set()
            for beat_id in beat_refs:
                beat = beats_by_id.get(beat_id)
                if beat:
                    required_evidence.update(str(ref) for ref in beat.get("evidence_refs", []))
            missing_evidence = required_evidence - set(evidence_refs)
            if missing_evidence:
                errors.append(problem("slide_evidence_gap", f"{owner} omits beat evidence: {', '.join(sorted(missing_evidence))}."))

        if len(numbers) != len(set(numbers)):
            errors.append(problem("duplicate_slide_number", "Slide numbers must be unique."))
        if numbers and sorted(numbers) != list(range(1, len(numbers) + 1)):
            errors.append(problem("slide_sequence", "Slide numbers must form a continuous 1..N sequence."))

        core_ids = {item["id"] for item in beats if item.get("priority") == "core"}
        uncovered = core_ids - covered_beats
        for beat_id in sorted(uncovered):
            errors.append(problem("core_beat_uncovered", f"Core manuscript beat {beat_id} has no slide."))
        core_coverage = 100.0 if not core_ids else 100.0 * len(core_ids & covered_beats) / len(core_ids)
        optional_uncovered = {
            item["id"] for item in beats if item.get("priority") in {"support", "optional"}
        } - covered_beats
        if optional_uncovered:
            warnings.append(problem("noncore_uncovered", f"Non-core beats omitted from slides: {', '.join(sorted(optional_uncovered))}."))

    return {
        "status": "failed" if errors else "passed",
        "stage": stage,
        "errors": errors,
        "warnings": warnings,
        "metrics": {
            "speaking_budget_seconds": budget,
            "outline_seconds": outline_seconds,
            "manuscript_seconds": beat_seconds,
            "evidence_items": len(evidence),
            "outline_sections": len(outline),
            "beats": len(beats),
            "slides": len(slides),
            "core_beat_coverage_percent": core_coverage,
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate the academic report production pipeline.")
    parser.add_argument("spec", help="Path to report-spec.json")
    parser.add_argument("--stage", choices=("outline", "manuscript", "slides"), required=True)
    parser.add_argument("--strict", action="store_true", help="Return non-zero when errors exist")
    parser.add_argument("--json-output", help="Write the complete report to this path")
    args = parser.parse_args()

    try:
        result = validate_pipeline(load_spec(Path(args.spec)), args.stage)
    except ValueError as exc:
        print(str(exc), file=sys.stderr)
        return 2
    if args.json_output:
        output = Path(args.json_output)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    metrics = result["metrics"]
    print(
        f"status={result['status']} stage={args.stage} errors={len(result['errors'])} "
        f"warnings={len(result['warnings'])} core_coverage={metrics['core_beat_coverage_percent']:.0f}%"
    )
    for item in result["errors"]:
        print(f"ERROR {item['code']}: {item['message']}")
    for item in result["warnings"]:
        print(f"WARN {item['code']}: {item['message']}")
    return 1 if args.strict and result["errors"] else 0


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Render readable outline, manuscript, slide plan, and rehearsal script."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


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


def evidence_index(data: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {
        str(item.get("id")): item
        for item in data.get("evidence", [])
        if isinstance(item, dict) and item.get("id")
    }


def reference_lines(refs: list[Any], evidence: dict[str, dict[str, Any]]) -> list[str]:
    lines: list[str] = []
    for raw in refs:
        ref = str(raw)
        item = evidence.get(ref, {})
        source = item.get("source", "[missing source]")
        claim = item.get("claim", "[missing claim]")
        lines.append(f"- {ref} · {source} · {claim}")
    return lines or ["- 无"]


def render_outline(data: dict[str, Any]) -> str:
    evidence = evidence_index(data)
    lines = [
        "# 汇报内容大纲",
        "",
        f"- 场景：{data.get('scenario', '')}",
        f"- 身份：{data.get('stance', '')}",
        f"- 总时长：{data.get('duration_minutes', '')} 分钟",
        f"- 提问预留：{data.get('qa_minutes', 0)} 分钟",
        "",
    ]
    for item in data.get("outline", []):
        if not isinstance(item, dict):
            continue
        lines.extend(
            [
                f"## {item.get('id', '')}｜{item.get('title', '')}",
                "",
                f"- 目的：{item.get('purpose', '')}",
                f"- 时间：{item.get('estimated_seconds', '')} 秒",
                "- 依据：",
                *reference_lines(item.get("evidence_refs", []), evidence),
                "",
            ]
        )
    return "\n".join(lines).rstrip() + "\n"


def render_manuscript(data: dict[str, Any]) -> str:
    evidence = evidence_index(data)
    outline = {
        str(item.get("id")): str(item.get("title", ""))
        for item in data.get("outline", [])
        if isinstance(item, dict)
    }
    lines = ["# 汇报文稿", ""]
    for item in data.get("beats", []):
        if not isinstance(item, dict):
            continue
        outline_id = str(item.get("outline_id", ""))
        lines.extend(
            [
                f"## {item.get('id', '')}｜{item.get('title', '')}",
                "",
                f"- 所属章节：{outline_id} · {outline.get(outline_id, '')}",
                f"- 类型：{item.get('type', '')}",
                f"- 优先级：{item.get('priority', '')}",
                f"- 目的：{item.get('purpose', '')}",
                f"- 时间：{item.get('estimated_seconds', '')} 秒",
                f"- 候选视觉：{'、'.join(str(x) for x in item.get('visual_candidates', [])) or '无'}",
                "- 依据：",
                *reference_lines(item.get("evidence_refs", []), evidence),
                "",
                str(item.get("spoken_text", "")),
                "",
            ]
        )
    return "\n".join(lines).rstrip() + "\n"


def render_slide_plan(data: dict[str, Any]) -> str:
    lines = ["# 页面脚本", ""]
    slides = sorted(
        (item for item in data.get("slides", []) if isinstance(item, dict)),
        key=lambda item: int(item.get("number", 0)),
    )
    for item in slides:
        lines.extend(
            [
                f"## Slide {item.get('number', '')} · {item.get('id', '')}｜{item.get('title', '')}",
                "",
                f"- 页面角色：{item.get('role', '')}",
                f"- 章节：{item.get('section_id', '')}",
                f"- 讲述单元：{', '.join(str(x) for x in item.get('beat_refs', [])) or '无'}",
                f"- 证据：{', '.join(str(x) for x in item.get('evidence_refs', [])) or '无'}",
                f"- 素材：{', '.join(str(x) for x in item.get('asset_refs', [])) or '无'}",
                f"- 模板布局：{item.get('template_layout', '')}",
                f"- 布局理由：{item.get('layout_rationale', '')}",
                f"- 布局风险：{item.get('layout_risk', '')}",
                f"- 图表任务：{item.get('exhibit_purpose', '') or '无'}",
                f"- 关键发现：{item.get('key_finding', '') or '无'}",
                f"- 时间：{item.get('estimated_seconds', '')} 秒",
                f"- 屏幕文字：{'｜'.join(str(x) for x in item.get('on_screen', [])) or '无'}",
                f"- 视觉：{'｜'.join(str(x) for x in item.get('visuals', [])) or '无'}",
                "",
            ]
        )
    return "\n".join(lines).rstrip() + "\n"


def render_rehearsal_script(data: dict[str, Any]) -> str:
    lines = [
        "# 最终排练稿",
        "",
        f"- 汇报场景：{data.get('scenario', '')}",
        f"- 可用讲述时间：{float(data.get('duration_minutes', 0) - data.get('qa_minutes', 0)):g} 分钟",
        "",
    ]
    slides = sorted(
        (item for item in data.get("slides", []) if isinstance(item, dict)),
        key=lambda item: int(item.get("number", 0)),
    )
    for item in slides:
        lines.extend(
            [
                f"## Slide {item.get('number', '')}｜{item.get('title', '')}",
                "",
                f"- 时间：{item.get('estimated_seconds', '')} 秒",
                f"- 对应讲述单元：{', '.join(str(x) for x in item.get('beat_refs', [])) or '无'}",
                f"- 视觉关注点：{item.get('key_finding', '') or '无'}",
                f"- 切页提示：{item.get('advance_cue', '') or '讲完本页后自然切换'}",
                "",
                str(item.get("speaker_notes", "")),
                "",
            ]
        )
    return "\n".join(lines).rstrip() + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description="Render readable pipeline documents.")
    parser.add_argument("spec", help="Path to report-spec.json")
    parser.add_argument("--outdir", default=".", help="Output directory")
    args = parser.parse_args()
    try:
        data = load_spec(Path(args.spec))
    except ValueError as exc:
        print(str(exc), file=sys.stderr)
        return 2
    outdir = Path(args.outdir)
    outdir.mkdir(parents=True, exist_ok=True)
    outputs = {
        "content-outline.md": render_outline(data),
        "talk-manuscript.md": render_manuscript(data),
        "slide-plan.md": render_slide_plan(data),
        "rehearsal-script.md": render_rehearsal_script(data),
    }
    for name, content in outputs.items():
        (outdir / name).write_text(content, encoding="utf-8")
    print("rendered=" + ",".join(outputs))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

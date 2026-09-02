#!/usr/bin/env python3
"""Audit an academic PPTX for structural and hidden-text hygiene.

Text-extraction portions are adapted from Knowledge Cat PPT's
``extract_pptx_text.py`` (MIT License, Copyright (c) 2026 Knowledge Cat
contributors). See references/THIRD_PARTY_NOTICES.md.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
import tempfile
import zipfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable
from xml.etree import ElementTree


A_NS = "http://schemas.openxmlformats.org/drawingml/2006/main"
P_NS = "http://schemas.openxmlformats.org/presentationml/2006/main"
A_P = f"{{{A_NS}}}p"
A_T = f"{{{A_NS}}}t"
P_SP = f"{{{P_NS}}}sp"
P_SPPR = f"{{{P_NS}}}spPr"
A_XFRM = f"{{{A_NS}}}xfrm"
A_OFF = f"{{{A_NS}}}off"
A_EXT = f"{{{A_NS}}}ext"
P_SLD_SZ = f"{{{P_NS}}}sldSz"

SLIDE_XML_RE = re.compile(r"ppt/slides/slide(\d+)\.xml$")
TEXT_PART_RE = re.compile(
    r"^(?:ppt/(?:slides|notesSlides|slideMasters|slideLayouts)/.+\.xml|docProps/.+\.xml)$"
)

PLACEHOLDER_PATTERNS = (
    re.compile(r"\b(?:x{3,}|lorem|ipsum|placeholder|todo|tbd|tbc)\b", re.I),
    re.compile(r"replace\s+(?:this|with)|click\s+to\s+add|type\s+(?:text|title)", re.I),
    re.compile(r"^\s*(?:这里输入|此处输入|请输入|输入(?:标题|小标题|正文|内容|文本|说明)|填写(?:标题|小标题|正文|内容|文本|说明)).*$"),
    re.compile(r"^\s*(?:答辩人|汇报人|指导老师|指导教师|姓名|单位|院系|专业|日期)\s*[:：]\s*$"),
    re.compile(r"^\s*(?:占位|待填写|待补充|示例文本)\s*$"),
)


@dataclass(frozen=True)
class PartText:
    part: str
    lines: list[str]


def normalize_text(value: str) -> str:
    return re.sub(r"\s+", " ", value).strip()


def slide_number(name: str) -> int:
    match = SLIDE_XML_RE.match(name)
    if not match:
        raise ValueError(f"Not a slide XML path: {name}")
    return int(match.group(1))


def parse_xml(xml_bytes: bytes, part: str) -> ElementTree.Element:
    try:
        return ElementTree.fromstring(xml_bytes)
    except ElementTree.ParseError as exc:
        raise ValueError(f"Invalid XML in {part}: {exc}") from exc


def extract_drawing_lines(root: ElementTree.Element) -> list[str]:
    lines: list[str] = []
    for paragraph in root.iter(A_P):
        line = normalize_text("".join(node.text or "" for node in paragraph.iter(A_T)))
        if line:
            lines.append(line)
    return lines


def extract_generic_leaf_text(root: ElementTree.Element) -> list[str]:
    lines: list[str] = []
    for node in root.iter():
        if len(node) == 0 and node.text:
            line = normalize_text(node.text)
            if line:
                lines.append(line)
    return lines


def issue(code: str, message: str, **extra: Any) -> dict[str, Any]:
    return {"code": code, "message": message, **extra}


def contains_term(lines: Iterable[str], term: str) -> bool:
    needle = normalize_text(term).casefold()
    return any(needle in normalize_text(line).casefold() for line in lines)


def placeholder_hits(parts: list[PartText], custom_terms: list[str]) -> list[dict[str, Any]]:
    hits: list[dict[str, Any]] = []
    for part in parts:
        for line in part.lines:
            matched = any(pattern.search(line) for pattern in PLACEHOLDER_PATTERNS)
            custom = next((term for term in custom_terms if term and contains_term([line], term)), None)
            if matched or custom:
                hits.append(issue("placeholder_text", f"Placeholder-like text: {line}", part=part.part, text=line))
    return hits


def read_slide_size(archive: zipfile.ZipFile) -> tuple[int, int] | None:
    name = "ppt/presentation.xml"
    if name not in archive.namelist():
        return None
    root = parse_xml(archive.read(name), name)
    node = root.find(f".//{P_SLD_SZ}")
    if node is None:
        return None
    try:
        return int(node.attrib["cx"]), int(node.attrib["cy"])
    except (KeyError, ValueError):
        return None


def shape_text(shape: ElementTree.Element) -> list[str]:
    return extract_drawing_lines(shape)


def off_canvas_text_hits(
    root: ElementTree.Element,
    part: str,
    slide_size: tuple[int, int] | None,
) -> list[dict[str, Any]]:
    if slide_size is None:
        return []
    slide_w, slide_h = slide_size
    hits: list[dict[str, Any]] = []
    for shape in root.iter(P_SP):
        lines = shape_text(shape)
        if not lines:
            continue
        sppr = shape.find(P_SPPR)
        if sppr is None:
            continue
        xfrm = sppr.find(A_XFRM)
        if xfrm is None:
            continue
        off = xfrm.find(A_OFF)
        ext = xfrm.find(A_EXT)
        if off is None or ext is None:
            continue
        try:
            x = int(off.attrib["x"])
            y = int(off.attrib["y"])
            cx = int(ext.attrib["cx"])
            cy = int(ext.attrib["cy"])
        except (KeyError, ValueError):
            continue
        fully_outside = x >= slide_w or y >= slide_h or x + cx <= 0 or y + cy <= 0
        if fully_outside:
            text = " | ".join(lines)
            hits.append(
                issue(
                    "off_canvas_text",
                    f"Text shape is fully outside the slide: {text}",
                    part=part,
                    text=text,
                    geometry={"x": x, "y": y, "cx": cx, "cy": cy},
                )
            )
    return hits


def load_manifest(path: Path | None) -> dict[str, Any]:
    if path is None:
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise ValueError(f"Manifest not found: {path}") from exc
    except json.JSONDecodeError as exc:
        raise ValueError(f"Invalid manifest JSON: {exc}") from exc
    if not isinstance(data, dict):
        raise ValueError("Manifest root must be an object.")
    return data


def audit_pptx(path: Path, manifest: dict[str, Any]) -> dict[str, Any]:
    if not path.exists():
        raise ValueError(f"PPTX not found: {path}")
    if path.suffix.lower() != ".pptx":
        raise ValueError(f"Expected a .pptx file: {path}")

    errors: list[dict[str, Any]] = []
    warnings: list[dict[str, Any]] = []
    slides: list[dict[str, Any]] = []
    parts: list[PartText] = []

    try:
        with zipfile.ZipFile(path) as archive:
            names = archive.namelist()
            slide_names = sorted(
                (name for name in names if SLIDE_XML_RE.match(name)), key=slide_number
            )
            if not slide_names:
                raise ValueError("No ppt/slides/slide*.xml files found.")

            slide_size = read_slide_size(archive)
            for name in names:
                if not TEXT_PART_RE.match(name):
                    continue
                root = parse_xml(archive.read(name), name)
                lines = extract_drawing_lines(root)
                if name.startswith("docProps/"):
                    lines = extract_generic_leaf_text(root)
                parts.append(PartText(name, lines))
                if SLIDE_XML_RE.match(name):
                    number = slide_number(name)
                    slides.append({"slide": number, "text": lines})
                    errors.extend(off_canvas_text_hits(root, name, slide_size))
    except zipfile.BadZipFile as exc:
        raise ValueError(f"Not a valid PPTX zip package: {path}") from exc

    slide_map = {int(slide["slide"]): list(slide["text"]) for slide in slides}
    custom_placeholders = [str(x) for x in manifest.get("placeholder_terms", [])]
    errors.extend(placeholder_hits(parts, custom_placeholders))

    expected_count = manifest.get("expected_slide_count")
    if isinstance(expected_count, int) and expected_count != len(slides):
        errors.append(issue("slide_count", f"Expected {expected_count} slides, found {len(slides)}."))

    cover = manifest.get("cover", {})
    if isinstance(cover, dict):
        for term in cover.get("required_terms", []):
            term = str(term)
            if term and not contains_term(slide_map.get(1, []), term):
                errors.append(issue("missing_cover_term", f"Cover is missing required value: {term}", slide=1, term=term))

    navigation = manifest.get("navigation", {})
    if isinstance(navigation, dict):
        sections = [str(x) for x in navigation.get("sections", []) if str(x)]
        required_on = navigation.get("required_on", [])
        if not isinstance(required_on, list):
            errors.append(issue("manifest_navigation", "navigation.required_on must be an array."))
        else:
            for raw_number in required_on:
                try:
                    number = int(raw_number)
                except (TypeError, ValueError):
                    errors.append(issue("manifest_navigation", f"Invalid slide number: {raw_number!r}"))
                    continue
                lines = slide_map.get(number)
                if lines is None:
                    errors.append(issue("missing_navigation_slide", f"Navigation requires missing slide {number}.", slide=number))
                    continue
                for section in sections:
                    if not contains_term(lines, section):
                        errors.append(issue("missing_navigation_term", f"Slide {number} is missing navigation label: {section}", slide=number, term=section))

    closing = manifest.get("closing", {})
    if isinstance(closing, dict) and closing:
        mode = closing.get("mode")
        conclusion_slide = closing.get("conclusion_slide")
        closing_slide = closing.get("closing_slide")
        if mode == "separate":
            if not isinstance(conclusion_slide, int) or not isinstance(closing_slide, int):
                errors.append(issue("manifest_closing", "Separate closing requires integer conclusion_slide and closing_slide."))
            elif conclusion_slide == closing_slide or closing_slide <= conclusion_slide:
                errors.append(issue("closing_order", "Closing slide must be a distinct slide after the conclusion."))
        for key, number_key in (("conclusion_terms", conclusion_slide), ("closing_terms", closing_slide)):
            if isinstance(number_key, int):
                lines = slide_map.get(number_key, [])
                for term in closing.get(key, []):
                    term = str(term)
                    if term and not contains_term(lines, term):
                        errors.append(issue("missing_closing_term", f"Slide {number_key} is missing required term: {term}", slide=number_key, term=term))

    forbidden_terms = [str(x) for x in manifest.get("forbidden_terms", []) if str(x)]
    for part in parts:
        for term in forbidden_terms:
            if contains_term(part.lines, term):
                errors.append(issue("forbidden_term", f"Forbidden or stale term found: {term}", part=part.part, term=term))

    if not manifest:
        warnings.append(issue("manifest_missing", "No report-spec manifest was supplied; cover, navigation, stale terms, and closing structure were not checked."))
    if not any(part.part.startswith("ppt/notesSlides/") for part in parts):
        warnings.append(issue("notes_absent", "No speaker-note XML parts were found; this is acceptable unless notes were required."))

    return {
        "status": "failed" if errors else "passed",
        "pptx": str(path.resolve()),
        "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
        "file_size_bytes": path.stat().st_size,
        "slide_count": len(slides),
        "errors": errors,
        "warnings": warnings,
        "slides": slides,
    }


def write_fixture(path: Path, placeholder: bool) -> None:
    width, height = 12_192_000, 6_858_000
    marker = "这里输入小标题" if placeholder else "研究结果来自真实材料"
    x = 13_000_000 if placeholder else 500_000
    slide = f'''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<p:sld xmlns:a="{A_NS}" xmlns:p="{P_NS}"><p:cSld><p:spTree>
<p:sp><p:spPr><a:xfrm><a:off x="{x}" y="500000"/><a:ext cx="2000000" cy="500000"/></a:xfrm></p:spPr>
<p:txBody><a:p><a:r><a:t>{marker}</a:t></a:r></a:p></p:txBody></p:sp>
</p:spTree></p:cSld></p:sld>'''
    presentation = f'''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<p:presentation xmlns:p="{P_NS}"><p:sldSz cx="{width}" cy="{height}"/></p:presentation>'''
    with zipfile.ZipFile(path, "w") as archive:
        archive.writestr("ppt/presentation.xml", presentation)
        archive.writestr("ppt/slides/slide1.xml", slide)


def run_self_test() -> int:
    with tempfile.TemporaryDirectory(prefix="academic-report-pptx-") as temp_dir:
        clean = Path(temp_dir) / "clean.pptx"
        bad = Path(temp_dir) / "bad.pptx"
        write_fixture(clean, placeholder=False)
        write_fixture(bad, placeholder=True)
        clean_result = audit_pptx(clean, {})
        bad_result = audit_pptx(bad, {})
    if clean_result["status"] != "passed":
        print(f"Clean fixture failed: {clean_result['errors']}", file=sys.stderr)
        return 1
    codes = {item["code"] for item in bad_result["errors"]}
    if not {"placeholder_text", "off_canvas_text"}.issubset(codes):
        print(f"Bad fixture did not trigger expected checks: {codes}", file=sys.stderr)
        return 1
    print("PPTX audit self-test passed.")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Audit an editable academic PPTX.")
    parser.add_argument("pptx", nargs="?", help="Path to the .pptx file")
    parser.add_argument("--manifest", help="Path to report-spec.json")
    parser.add_argument("--json-output", help="Write the full audit report to this path")
    parser.add_argument("--strict", action="store_true", help="Return non-zero when blocking errors exist")
    parser.add_argument("--self-test", action="store_true", help="Run bundled synthetic checks")
    args = parser.parse_args()

    if args.self_test:
        return run_self_test()
    if not args.pptx:
        parser.error("pptx is required unless --self-test is used")

    try:
        manifest = load_manifest(Path(args.manifest)) if args.manifest else {}
        result = audit_pptx(Path(args.pptx), manifest)
    except ValueError as exc:
        print(str(exc), file=sys.stderr)
        return 2

    if args.json_output:
        output_path = Path(args.json_output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"status={result['status']} slides={result['slide_count']} errors={len(result['errors'])} warnings={len(result['warnings'])}")
    for item in result["errors"]:
        print(f"ERROR {item['code']}: {item['message']}")
    for item in result["warnings"]:
        print(f"WARN {item['code']}: {item['message']}")
    if args.strict and result["errors"]:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

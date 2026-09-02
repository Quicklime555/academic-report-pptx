from __future__ import annotations

import importlib.util
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path


SKILL_DIR = Path(__file__).resolve().parents[1]
SCRIPT_PATH = SKILL_DIR / "scripts" / "audit_pptx.py"
SPEC = importlib.util.spec_from_file_location("audit_pptx", SCRIPT_PATH)
assert SPEC and SPEC.loader
audit_pptx = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = audit_pptx
SPEC.loader.exec_module(audit_pptx)


def slide_xml(lines: list[str], x: int = 500_000) -> str:
    paragraphs = "".join(
        f"<a:p><a:r><a:t>{line}</a:t></a:r></a:p>" for line in lines
    )
    return f'''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<p:sld xmlns:a="{audit_pptx.A_NS}" xmlns:p="{audit_pptx.P_NS}"><p:cSld><p:spTree>
<p:sp><p:spPr><a:xfrm><a:off x="{x}" y="500000"/><a:ext cx="5000000" cy="1000000"/></a:xfrm></p:spPr>
<p:txBody>{paragraphs}</p:txBody></p:sp>
</p:spTree></p:cSld></p:sld>'''


def write_pptx(path: Path, slides: list[str], extras: dict[str, str] | None = None) -> None:
    presentation = f'''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<p:presentation xmlns:p="{audit_pptx.P_NS}"><p:sldSz cx="12192000" cy="6858000"/></p:presentation>'''
    with zipfile.ZipFile(path, "w") as archive:
        archive.writestr("ppt/presentation.xml", presentation)
        for index, xml in enumerate(slides, start=1):
            archive.writestr(f"ppt/slides/slide{index}.xml", xml)
        for name, xml in (extras or {}).items():
            archive.writestr(name, xml)


class AuditPptxTests(unittest.TestCase):
    def test_self_test(self) -> None:
        self.assertEqual(audit_pptx.run_self_test(), 0)

    def test_clean_manifest_passes(self) -> None:
        manifest = {
            "expected_slide_count": 2,
            "cover": {"required_terms": ["真实题目", "张三", "某大学", "2026年9月"]},
            "navigation": {
                "sections": ["研究背景", "研究设计", "结论"],
                "required_on": [2],
            },
            "closing": {
                "mode": "conclusion",
                "conclusion_slide": 2,
                "conclusion_terms": ["结论"],
            },
            "forbidden_terms": ["旧论文题目"],
        }
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "clean.pptx"
            write_pptx(
                path,
                [
                    slide_xml(["真实题目", "张三", "某大学", "2026年9月"]),
                    slide_xml(["研究背景", "研究设计", "结论", "结果来自真实材料"]),
                ],
            )
            result = audit_pptx.audit_pptx(path, manifest)
        self.assertEqual(result["status"], "passed", result["errors"])

    def test_hidden_residue_and_structure_fail(self) -> None:
        layout = f'''<p:sldLayout xmlns:a="{audit_pptx.A_NS}" xmlns:p="{audit_pptx.P_NS}">
<p:cSld><p:spTree><p:sp><p:txBody><a:p><a:r><a:t>旧论文题目</a:t></a:r></a:p></p:txBody></p:sp></p:spTree></p:cSld></p:sldLayout>'''
        manifest = {
            "expected_slide_count": 2,
            "cover": {"required_terms": ["张三"]},
            "navigation": {"sections": ["背景", "结果"], "required_on": [2]},
            "forbidden_terms": ["旧论文题目"],
        }
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "bad.pptx"
            write_pptx(
                path,
                [slide_xml(["题目"]), slide_xml(["这里输入小标题"], x=13_000_000)],
                {"ppt/slideLayouts/slideLayout1.xml": layout},
            )
            result = audit_pptx.audit_pptx(path, manifest)
        codes = {item["code"] for item in result["errors"]}
        self.assertTrue(
            {"placeholder_text", "off_canvas_text", "forbidden_term", "missing_cover_term", "missing_navigation_term"}.issubset(codes),
            codes,
        )


if __name__ == "__main__":
    unittest.main()

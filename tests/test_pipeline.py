import importlib.util
import json
import tempfile
import unittest
from copy import deepcopy
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def load_module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


validator = load_module("validate_pipeline", ROOT / "scripts" / "validate_pipeline.py")
renderer = load_module("render_pipeline_docs", ROOT / "scripts" / "render_pipeline_docs.py")


def valid_spec():
    return {
        "version": 2,
        "scenario": "thesis defense",
        "stance": "author",
        "language": "zh-CN",
        "duration_minutes": 10,
        "qa_minutes": 2,
        "expected_slide_count": 2,
        "evidence": [
            {"id": "E001", "kind": "result", "source": "Figure 2", "claim": "Accuracy improved."}
        ],
        "outline": [
            {
                "id": "O01",
                "title": "主要结果",
                "purpose": "说明核心发现",
                "estimated_seconds": 120,
                "evidence_refs": ["E001"],
            }
        ],
        "beats": [
            {
                "id": "B001",
                "outline_id": "O01",
                "type": "content",
                "priority": "core",
                "title": "核心发现",
                "purpose": "解释结果",
                "spoken_text": "实验结果显示准确率提高。",
                "estimated_seconds": 60,
                "evidence_refs": ["E001"],
                "visual_candidates": ["Figure 2"],
            }
        ],
        "slides": [
            {
                "id": "S001",
                "number": 1,
                "role": "cover",
                "title": "答辩汇报",
                "template_layout": "cover",
                "estimated_seconds": 10,
                "beat_refs": [],
                "evidence_refs": [],
                "on_screen": ["答辩汇报"],
                "visuals": [],
            },
            {
                "id": "S002",
                "number": 2,
                "role": "content",
                "section_id": "O01",
                "title": "主要结果",
                "template_layout": "evidence",
                "estimated_seconds": 60,
                "beat_refs": ["B001"],
                "evidence_refs": ["E001"],
                "on_screen": ["准确率提高"],
                "visuals": ["Figure 2"],
            },
        ],
    }


class PipelineTests(unittest.TestCase):
    def test_valid_spec_passes_all_stages(self):
        data = valid_spec()
        for stage in ("outline", "manuscript", "slides"):
            result = validator.validate_pipeline(data, stage)
            self.assertEqual("passed", result["status"], result["errors"])
        self.assertEqual(100.0, result["metrics"]["core_beat_coverage_percent"])

    def test_core_beat_must_be_covered(self):
        data = valid_spec()
        data["slides"][1]["beat_refs"] = []
        codes = {item["code"] for item in validator.validate_pipeline(data, "slides")["errors"]}
        self.assertIn("core_beat_uncovered", codes)

    def test_slide_carries_all_beat_evidence(self):
        data = valid_spec()
        data["slides"][1]["evidence_refs"] = []
        codes = {item["code"] for item in validator.validate_pipeline(data, "slides")["errors"]}
        self.assertIn("slide_evidence_gap", codes)

    def test_renderer_outputs_three_traceable_documents(self):
        data = valid_spec()
        with tempfile.TemporaryDirectory() as temp_dir:
            output = Path(temp_dir)
            (output / "content-outline.md").write_text(renderer.render_outline(data), encoding="utf-8")
            (output / "talk-manuscript.md").write_text(renderer.render_manuscript(data), encoding="utf-8")
            (output / "slide-plan.md").write_text(renderer.render_slide_plan(data), encoding="utf-8")
            self.assertIn("O01", (output / "content-outline.md").read_text(encoding="utf-8"))
            self.assertIn("B001", (output / "talk-manuscript.md").read_text(encoding="utf-8"))
            self.assertIn("S002", (output / "slide-plan.md").read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()

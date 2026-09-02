import importlib.util
import tempfile
import unittest
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
        "version": 3,
        "scenario": "thesis defense",
        "stance": "author",
        "language": "zh-CN",
        "duration_minutes": 10,
        "qa_minutes": 2,
        "expected_slide_count": 2,
        "evidence": [
            {"id": "E001", "kind": "result", "source": "Figure 2", "claim": "Accuracy improved."}
        ],
        "assets": [
            {
                "id": "A001",
                "source": "Figure 2",
                "geometry": "chart",
                "handling": "preserve",
                "evidence_refs": ["E001"],
            }
        ],
        "template": {
            "provided": True,
            "source": "school-template.pptx",
            "adherence": "strict",
            "profile": {
                "canvas": "16:9",
                "safe_margins": "0.5 inch",
                "theme_fonts": "Microsoft YaHei",
                "colors": "school blue and neutral gray",
                "page_families": ["cover", "evidence"],
                "navigation_footer": "existing footer",
                "risks": [],
            },
            "representative_review": {
                "required": True,
                "status": "approved",
                "slide_refs": ["S001", "S002"],
            },
        },
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
                "layout_rationale": "Use the official cover family.",
                "layout_risk": "none",
                "estimated_seconds": 10,
                "beat_refs": [],
                "evidence_refs": [],
                "asset_refs": [],
                "on_screen": ["答辩汇报"],
                "visuals": [],
                "speaker_notes": "各位老师好，下面开始汇报。",
            },
            {
                "id": "S002",
                "number": 2,
                "role": "content",
                "section_id": "O01",
                "title": "主要结果",
                "template_layout": "evidence",
                "layout_rationale": "The chart is the primary evidence.",
                "layout_risk": "axis labels may be small",
                "estimated_seconds": 60,
                "beat_refs": ["B001"],
                "evidence_refs": ["E001"],
                "asset_refs": ["A001"],
                "exhibit_purpose": "Use the result chart to support the core finding.",
                "key_finding": "Accuracy improved.",
                "on_screen": ["准确率提高"],
                "visuals": ["Figure 2"],
                "speaker_notes": "请看图中的核心结果，实验准确率得到提高。",
                "advance_cue": "解释完高亮数据点后切页",
            },
        ],
    }


class PipelineTests(unittest.TestCase):
    def test_valid_spec_passes_all_stages(self):
        data = valid_spec()
        for stage in ("outline", "manuscript", "slides", "delivery"):
            result = validator.validate_pipeline(data, stage)
            self.assertEqual("passed", result["status"], result["errors"])
        self.assertEqual(100.0, result["metrics"]["core_beat_coverage_percent"])
        self.assertEqual(100.0, result["metrics"]["rehearsal_ready_percent"])

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

    def test_delivery_requires_approved_representative_slides(self):
        data = valid_spec()
        data["template"]["representative_review"]["status"] = "pending"
        slide_result = validator.validate_pipeline(data, "slides")
        self.assertEqual("passed", slide_result["status"], slide_result["errors"])
        self.assertIn("representative_review_pending", {item["code"] for item in slide_result["warnings"]})
        delivery_codes = {item["code"] for item in validator.validate_pipeline(data, "delivery")["errors"]}
        self.assertIn("representative_review_pending", delivery_codes)

    def test_delivery_requires_page_aligned_speaker_notes(self):
        data = valid_spec()
        del data["slides"][1]["speaker_notes"]
        codes = {item["code"] for item in validator.validate_pipeline(data, "delivery")["errors"]}
        self.assertIn("missing_text", codes)

    def test_unresolved_asset_quality_blocks_delivery(self):
        data = valid_spec()
        data["assets"][0]["handling"] = "request-higher-resolution"
        codes = {item["code"] for item in validator.validate_pipeline(data, "delivery")["errors"]}
        self.assertIn("unresolved_asset_quality", codes)

    def test_visual_asset_requires_exhibit_task(self):
        data = valid_spec()
        del data["slides"][1]["exhibit_purpose"]
        codes = {item["code"] for item in validator.validate_pipeline(data, "slides")["errors"]}
        self.assertIn("missing_text", codes)

    def test_no_template_can_explicitly_skip_representative_review(self):
        data = valid_spec()
        data["template"] = {
            "provided": False,
            "adherence": "none",
            "representative_review": {
                "required": False,
                "status": "not-required",
                "slide_refs": [],
            },
        }
        result = validator.validate_pipeline(data, "delivery")
        self.assertEqual("passed", result["status"], result["errors"])

    def test_renderer_outputs_four_traceable_documents(self):
        data = valid_spec()
        with tempfile.TemporaryDirectory() as temp_dir:
            output = Path(temp_dir)
            (output / "content-outline.md").write_text(renderer.render_outline(data), encoding="utf-8")
            (output / "talk-manuscript.md").write_text(renderer.render_manuscript(data), encoding="utf-8")
            (output / "slide-plan.md").write_text(renderer.render_slide_plan(data), encoding="utf-8")
            (output / "rehearsal-script.md").write_text(renderer.render_rehearsal_script(data), encoding="utf-8")
            self.assertIn("O01", (output / "content-outline.md").read_text(encoding="utf-8"))
            self.assertIn("B001", (output / "talk-manuscript.md").read_text(encoding="utf-8"))
            self.assertIn("S002", (output / "slide-plan.md").read_text(encoding="utf-8"))
            rehearsal = (output / "rehearsal-script.md").read_text(encoding="utf-8")
            self.assertIn("Slide 2", rehearsal)
            self.assertIn("请看图中的核心结果", rehearsal)


if __name__ == "__main__":
    unittest.main()

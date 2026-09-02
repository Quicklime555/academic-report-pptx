# 大纲—文稿—页面契约

`report-spec.json` 是事实、讲述和页面之间的私有结构化合同。可读的 `content-outline.md`、`talk-manuscript.md` 和 `slide-plan.md` 由脚本从它生成，避免三份文档各自漂移。

## 稳定 ID

- 证据：`E001`、`E002`；
- 大纲章节：`O01`、`O02`；
- 讲述单元：`B001`、`B002`；
- 页面：`S001`、`S002`。

ID 一经用户确认不得重排复用。删除内容时保留其他 ID，不把旧 ID 指向新事实。

## 阶段一：内容大纲

先填写元数据、`evidence` 和 `outline`。每个大纲章节包含目的、时间和证据引用。大纲描述汇报逻辑，不写 PPT 页码。

```text
python scripts/validate_pipeline.py report-spec.json --stage outline --strict
python scripts/render_pipeline_docs.py report-spec.json --outdir .
```

向用户展示 `content-outline.md`，确认后才进入文稿阶段。

## 阶段二：汇报文稿

将大纲扩展为 `beats`。每个讲述单元包含：

- 所属大纲章节；
- 标题和讲述目的；
- 可直接用于排练的 `spoken_text`；
- 预计秒数；
- `core`、`support`、`optional` 或 `backup` 优先级；
- 证据引用和候选视觉；
- `content`、`opening`、`transition` 或 `closing` 类型。

文稿按讲述单元组织，不预设页码。`content` 单元必须引用证据；转场和开闭场可以没有学术证据。

```text
python scripts/validate_pipeline.py report-spec.json --stage manuscript --strict
python scripts/render_pipeline_docs.py report-spec.json --outdir .
```

向用户展示 `talk-manuscript.md`，确认后才进入页面阶段。

## 阶段三：页面脚本

`slides` 把讲述单元映射为页面。每页记录：

- 页面编号、角色、标题和所属章节；
- `beat_refs` 与 `evidence_refs`；
- 屏幕文字、候选视觉和来源；
- `template_layout`；
- 预计讲述时间。

除封面、目录、章节页、参考文献和纯结束页外，页面必须引用讲述单元。讲述单元使用的证据必须出现在对应页面的证据引用中。所有 `core` 讲述单元必须至少进入一页。

```text
python scripts/validate_pipeline.py report-spec.json --stage slides --strict
python scripts/render_pipeline_docs.py report-spec.json --outdir .
```

校验通过后，`slide-plan.md` 才能作为 PPTX 制作输入。

## 最小结构

```json
{
  "version": 2,
  "scenario": "thesis-defense",
  "stance": "author",
  "language": "zh-CN",
  "duration_minutes": 15,
  "qa_minutes": 3,
  "evidence": [
    {
      "id": "E001",
      "kind": "paper",
      "source": "thesis.pdf · p. 12",
      "claim": "材料直接支持的事实",
      "boundary": "不能据此推出的内容"
    }
  ],
  "outline": [
    {
      "id": "O01",
      "title": "研究问题",
      "purpose": "让听众理解本研究要解决什么",
      "estimated_seconds": 90,
      "evidence_refs": ["E001"]
    }
  ],
  "beats": [
    {
      "id": "B001",
      "outline_id": "O01",
      "type": "content",
      "title": "现有方法在目标条件下仍有缺口",
      "purpose": "提出研究问题",
      "spoken_text": "可直接用于排练的讲述文稿。",
      "estimated_seconds": 45,
      "priority": "core",
      "evidence_refs": ["E001"],
      "visual_candidates": ["论文 Figure 1"]
    }
  ],
  "expected_slide_count": 2,
  "slides": [
    {
      "id": "S001",
      "number": 1,
      "role": "cover",
      "title": "真实汇报题目",
      "section_id": null,
      "beat_refs": [],
      "evidence_refs": [],
      "on_screen": ["张三", "某大学某学院"],
      "visuals": [],
      "template_layout": "cover-01",
      "estimated_seconds": 15
    },
    {
      "id": "S002",
      "number": 2,
      "role": "content",
      "title": "现有方法在目标条件下仍有缺口",
      "section_id": "O01",
      "beat_refs": ["B001"],
      "evidence_refs": ["E001"],
      "on_screen": ["一句核心结论"],
      "visuals": ["论文 Figure 1"],
      "template_layout": "figure-right-01",
      "estimated_seconds": 45
    }
  ]
}
```

封面、导航、结束方式、禁词和占位词字段继续按 `references/report-contract.md` 填写，供最终 PPTX 审计使用。

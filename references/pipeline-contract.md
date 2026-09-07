# 大纲—文稿—页面契约

`report-spec.json` 是事实、讲述、素材、模板和页面之间的私有结构化合同。可读的 `content-outline.md`、`talk-manuscript.md`、`slide-plan.md` 和 `rehearsal-script.md` 由脚本从它生成，避免各份文档漂移。

## 稳定 ID

- 证据：`E001`、`E002`；
- 素材：`A001`、`A002`；
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

新策划的大纲向用户展示并确认后进入文稿阶段。用户已提供明确且确认的大纲时，复用其内容并补齐映射，不重复索取相同确认。

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

新写或实质改写的母稿向用户展示并确认后进入页面阶段。已有明确确认的讲稿可直接进入分页；只修改现有 PPT 时保留未变内容，仅同步受影响的页面与讲稿，不以重写母稿作为修改前提。

## 阶段三：页面脚本

先完成 `assets` 与 `template`：关键素材记录来源、证据、几何形态与处理方式；模板记录继承等级、profile 和代表页计划。再由 `slides` 把讲述单元映射为页面。

`slides` 把讲述单元映射为页面。每页记录：

- 页面编号、角色、标题和所属章节；
- `beat_refs`、`evidence_refs` 与 `asset_refs`；
- 屏幕文字、候选视觉和来源；
- 图表任务和听众应看到的关键发现；
- `template_layout`、布局理由和风险；
- 预计讲述时间。

除封面、目录、章节页、参考文献和纯结束页外，页面必须引用讲述单元。讲述单元使用的证据必须出现在对应页面的证据引用中。所有 `core` 讲述单元必须至少进入一页。

```text
python scripts/validate_pipeline.py report-spec.json --stage slides --strict
python scripts/render_pipeline_docs.py report-spec.json --outdir .
```

校验通过后，`slide-plan.md` 才能作为 PPTX 制作输入。

页面计划阶段允许代表页状态为 `pending`，但必须产生警告。

## 阶段四：最终交付

代表页确认和全稿修订完成后，为每页写入 `speaker_notes`，必要时补充 `advance_cue`。逐页文稿来自已确认讲述单元，但可按最终页面重新组织措辞；不得增加新的学术主张。

```text
python scripts/validate_pipeline.py report-spec.json --stage delivery --strict
python scripts/render_pipeline_docs.py report-spec.json --outdir .
```

`delivery` 阶段要求：代表页关卡已通过或明确不需要、所有页面都有排练文稿、素材高清风险已解决、页面总时间不超预算。校验通过后，`rehearsal-script.md` 与最终 PPTX 成套交付。

## 最小结构

```json
{
  "version": 3,
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
  "assets": [
    {
      "id": "A001",
      "source": "thesis.pdf · Figure 1",
      "geometry": "wide",
      "handling": "preserve",
      "evidence_refs": ["E001"]
    }
  ],
  "template": {
    "provided": true,
    "source": "official-template.pptx",
    "adherence": "strict",
    "profile": {
      "canvas": "16:9",
      "safe_margins": "沿用模板安全区",
      "theme_fonts": "沿用模板主题字体",
      "colors": "沿用机构色和语义色",
      "page_families": ["cover", "evidence", "conclusion"],
      "navigation_footer": "沿用原导航和页脚",
      "risks": []
    },
    "representative_review": {
      "required": true,
      "status": "approved",
      "slide_refs": ["S001", "S002"]
    }
  },
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
      "asset_refs": [],
      "on_screen": ["张三", "某大学某学院"],
      "visuals": [],
      "template_layout": "cover-01",
      "layout_rationale": "使用官方封面家族",
      "layout_risk": "无",
      "estimated_seconds": 15,
      "speaker_notes": "各位老师好，下面开始汇报。"
    },
    {
      "id": "S002",
      "number": 2,
      "role": "content",
      "title": "现有方法在目标条件下仍有缺口",
      "section_id": "O01",
      "beat_refs": ["B001"],
      "evidence_refs": ["E001"],
      "asset_refs": ["A001"],
      "exhibit_purpose": "用原论文图支持研究缺口",
      "key_finding": "现有方法在目标条件下仍有缺口",
      "on_screen": ["一句核心结论"],
      "visuals": ["论文 Figure 1"],
      "template_layout": "figure-right-01",
      "layout_rationale": "横向原图需要较宽证据区",
      "layout_risk": "图例可能过小",
      "estimated_seconds": 45,
      "speaker_notes": "请看这张图，关键限制出现在目标条件下。",
      "advance_cue": "指出高亮区域后切页"
    }
  ]
}
```

封面、导航、结束方式、禁词和占位词字段继续按 `references/report-contract.md` 填写，供最终 PPTX 审计使用。

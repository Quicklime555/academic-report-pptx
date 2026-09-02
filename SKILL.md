---
name: academic-report-pptx
description: "Create, extend, redesign, or repair evidence-grounded academic presentations as editable PPTX files through an outline → talk manuscript → slide plan workflow, preferably by extracting and extending a user-provided PowerPoint template. Use for literature reports, journal clubs, lab or group meetings, research progress reports, proposals, thesis defenses, conference or seminar talks, and other academic presentations that require factual traceability, restrained scientific styling, template fidelity, native editable objects, and final content/render/object QA. Also use when an existing academic PPTX must be made less AI-like while preserving its institutional visual language. Do not use for paper annotation or note management, paper summaries without slides, routine teaching courseware, marketing or investor decks, image-only slide generation, generic visual critique without PPT implementation, or requests where editable PPTX is not the intended deliverable."
---

# Academic Report PPT

先把汇报讲清楚，再把材料、文稿和模板编译成一套能讲、能改、能核对的学术 PPTX。场景可以是文献汇报、组会、研究进展、开题/答辩、会议报告或学术讲座；共同标准是证据约束、务实克制、模板优先和对象级可编辑。

## 开始前

1. 阅读 `references/report-contract.md`，确定场景、听众、时长、材料、汇报身份、模板与交付要求。
2. 阅读 `references/pipeline-contract.md`，建立证据、大纲、讲述单元和页面之间的稳定映射。
3. 阅读 `references/content-and-story.md`，确定各场景的内容与论证原则。
4. 阅读 `references/template-and-visual-system.md`，决定模板继承、页面家族和克制的科学视觉语言。
5. 在任务输出目录创建私有 `report-spec.json`。不要把用户身份、论文、任务路径或具体汇报内容写进本 Skill。

缺少支撑核心内容的论文、数据或用户材料时，不得把推测写成事实。缺少正式封面所需姓名、单位、场合或日期但用户要求成品时，先补齐这些字段。只有时长缺失时，可明确采用 12 分钟、16:9、中文、可编辑 PPTX 的工作假设。

## 工作流

### 1. 建立汇报契约

- 判定任务是从材料新建、基于模板延伸、改造现有学术 PPTX，还是三者组合。
- 判定汇报立场：作者汇报、第三方论文讲解、研究进展、方案/开题或答辩。不同立场不得混用“本文”“我们”和“作者”。
- 从当前任务材料建立 claim–evidence ledger；数字、图表、论文结论、汇报者解释和待验证内容必须区分。
- 在 `report-spec.json` 中先记录汇报元数据、封面字段和证据；章节、讲述单元、页面与模板映射在后续阶段依次补充。

### 2. 内容大纲

- 在 `report-spec.json` 中建立带稳定 ID 的证据和章节；运行 `scripts/validate_pipeline.py --stage outline`，再生成 `content-outline.md`。
- 大纲说明每一部分解决什么问题、使用哪些证据、预计占用多少时间，不提前按 PPT 页码切分。
- 向用户展示大纲并等待确认。用户已经提供明确且可核对的大纲时，复用它并补齐证据与时间字段。

### 3. 汇报文稿

- 把已确认大纲写成带稳定 ID 的讲述单元。每个单元记录口头文稿、证据、时间、优先级和候选视觉；它不是按页切开的文章。
- 运行 `scripts/validate_pipeline.py --stage manuscript`，再生成 `talk-manuscript.md`。
- 向用户展示文稿并等待确认。不得在后续分页时擅自增加文稿之外的学术判断。

### 4. 页面脚本

- 将讲述单元映射为页面。一个单元可以拆成多页，多个短单元可以合并；所有核心单元必须有明确页面去向。
- 每页记录讲述单元、证据、屏幕文字、视觉素材、时间和模板布局；页数由讲话时间、证据链和模板节奏共同决定。
- 运行 `scripts/validate_pipeline.py --stage slides`，并生成内部 `slide-plan.md`。校验通过前不得制作 PPTX。
- 内容原则见 `references/content-and-story.md`；不要机械按论文目录分页，也不要强迫所有页面使用口号式 action title。

### 5. 模板优先

- 用户提供 PPTX 模板时，先审计母版、版式、主题字体、颜色、页面家族、导航、页脚、备注、旧元数据、隐藏对象和残留内容，再写内容。
- 建立 template profile 和逐页 layout mapping；优先延伸已有页面家族，只有内容无法安全承载时才新增同语法布局。
- 如果模板存在无法清理的旧内容、锁定对象或不兼容结构，说明风险，并在得到用户同意后转为“提取视觉语法后从空白 16:9 重建”。
- 没有模板时使用克制的科学默认：稳定网格、少量语义色、清晰证据层级、可投影字号，不制造营销海报感。

### 6. 选定制作能力

阅读 `references/tool-adapters.md`。优先使用宿主已有的原生 PPTX 能力；在 Codex 中若 `ppt-master` 可用，新建使用 Generate PPTX，模板复刻/延伸使用 Create Template 或 Generate PPTX 的模板流程，修改既有文件使用 Beautify 或 Edit Native PPTX，并遵守该 Skill 自身的阻塞关卡。不要在本 Skill 内复制通用 PPTX 渲染引擎。

### 7. 制作和修订

- 文字、形状、表格和可重建图表使用原生可编辑对象。复杂显微图、照片、论文原图和无法可靠重建的数据图可保留为带来源的图片。
- 不得把整页位图、AI 生成的科学图或截图式背景冒充可编辑 PPTX。
- 原论文图和数据图优先；裁图保留必要坐标、图例、面板标识和来源，不包含无关论文正文。
- 颜色承担章节、研究对象、条件或证据状态的稳定语义，不随机装饰。封面和导航优先遵循用户模板与机构规范。
- 面向听众的页面不得出现内部提示词、路线名、生成说明、占位符或评价规则。

### 8. 交付前质量门

阅读 `references/quality-gates.md`，然后必须完成：

1. 渲染全部页面并检查 contact sheet；对封面、最密集证据页、关键图表页、结论页和结束页做全尺寸检查。
2. 重新运行 `scripts/validate_pipeline.py --stage slides`，确认核心讲述单元全部进入页面，页面没有超出文稿和证据。
3. 用 `scripts/audit_pptx.py` 对最终 PPTX 和 `report-spec.json` 做对象级文本、占位词、封面、导航、备注/母版、旧元数据和越界文本检查。
4. 修复后重新渲染并重新审计，直到没有 blocking error。
5. 重新打开最终 PPTX，确认页数、比例、字体、图片、对象可选择性和文件无修复警告。无法完成的检查必须列为未验证。

## 输出

默认交付：

- 一份对象级可编辑 `.pptx`；
- `content-outline.md`、`talk-manuscript.md` 和内部 `slide-plan.md`；
- 一份简短 `qa-report.md`，记录事实、模板、视觉、对象卫生和可编辑性检查；
- 任务目录内保留 `report-spec.json`、渲染页和 contact sheet 供追溯。

向用户说明成品、关键取舍、已完成检查、保留为图片的科学素材以及仍需本人核对的事实。不要把内部生产文档当作面向听众的交付物。

## 资源导航

- `references/report-contract.md`：开始任何任务前读取。
- `references/pipeline-contract.md`：创建大纲、文稿、页面脚本和运行一致性校验时读取。
- `references/content-and-story.md`：规划论证与证据页时读取。
- `references/template-and-visual-system.md`：分析模板、页面家族、导航和视觉语言时读取。
- `references/tool-adapters.md`：选择宿主可用的原生 PPTX 制作能力时读取。
- `references/quality-gates.md`：最终交付前读取。
- `references/THIRD_PARTY_NOTICES.md`：复制、发布或审计本 Skill 时读取；运行普通 PPT 任务时不需要。
- `scripts/audit_pptx.py`：对最终 PPTX 做确定性结构与对象卫生审计。
- `scripts/validate_pipeline.py`：检查证据、大纲、讲述单元与页面映射。
- `scripts/render_pipeline_docs.py`：从 `report-spec.json` 生成三份可读文档。

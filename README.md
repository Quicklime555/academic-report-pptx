# academic-report-pptx

不是把论文塞进模板。这个 Skill 会先把你准备怎么讲写清楚，再把材料、文稿和模板编译成一套真正能讲、能改、能核对的学术 PPTX。

适用于文献汇报、journal club、组会、研究进展、开题、答辩、会议和研讨会报告，也可以修复已有学术 PPTX 的 AI 感、模板残留和不可编辑问题。

## 四个核心卖点

- **能讲**：先确认内容大纲，再形成不预先按页切碎的口头文稿，最后才把讲述单元映射到页面。PPT 不再是一组互不相干的卡片。
- **像你**：优先提取用户模板的母版、页面家族、导航和排版语法，不只是换成相近配色。
- **能改**：普通文字、形状、表格和可重建图表保留为原生对象，不用整页图片伪装成 PPTX。
- **可核对**：证据、章节、讲述单元和页面使用稳定 ID 串联；交付前同时检查内容覆盖、视觉渲染和隐藏对象残留。

核心流程是：`证据 → 内容大纲 → 汇报文稿 → 页面脚本 → 模板布局 → 可编辑 PPTX`。其中证据台账约束“什么是真的”，汇报文稿约束“汇报者准备怎么讲”，二者共同约束最终页面。

## 安装

把仓库地址交给支持 Skills 的 Agent 安装：

```text
https://github.com/Quicklime555/academic-report-pptx
```

或者使用 Skills CLI：

```text
npx skills add Quicklime555/academic-report-pptx
```

安装后重新启动会话，确认 `academic-report-pptx` 已出现在可用 Skills 列表中。

## 首次配置

核心 Skill 不需要 API key。宿主必须具备创建、编辑、渲染和重新打开原生 PPTX 的能力；在 Codex 中推荐搭配已安装的 `ppt-master`。

## 使用示例

```text
参考学校给的答辩模板，把我的论文和实验图做成 15 分钟中文答辩 PPTX。事实要可核对，风格克制，保留可编辑对象，交付前检查旧模板残留。
```

```text
沿用这个实验室模板，把阶段结果扩成组会汇报。不要整页图片，图表和文字必须可编辑。
```

```text
先根据论文和 15 分钟要求给我内容大纲；确认后写成口头汇报文稿，最后再沿用学校模板制作可编辑答辩 PPTX。
```

## 兼容性与依赖

- 已验证：Windows 11、Codex、本地 Python 3.12、原生 PPTX 工作流。
- `scripts/audit_pptx.py` 只使用 Python 标准库；其他平台理论可运行，但尚未完成实际验证。
- 实际 PPTX 制作和渲染依赖宿主能力；只有整页图片生成能力时不能满足本 Skill 的核心承诺。

## 数据与边界

本 Skill 自带的流程校验和 PPTX 对象审计脚本在本机运行。是否联网、数据是否离开本机，取决于宿主实际采用的 PPTX 制作能力。

本 Skill 不负责论文批注或笔记管理、无 PPT 的论文总结、常规教学课件、营销/融资演示、纯图片幻灯片、只做审美点评而不实施 PPTX 修改的任务。

## 输出

- 对象级可编辑 `.pptx`；
- `content-outline.md`、`talk-manuscript.md` 和内部 `slide-plan.md`；
- `qa-report.md`；
- 任务目录中的 `report-spec.json`、流程校验 JSON、逐页渲染图、contact sheet 和对象审计 JSON。

## 测试

```text
python scripts/audit_pptx.py --self-test
python scripts/validate_pipeline.py <report-spec.json> --stage slides --strict
python -m unittest discover -s tests -v
```

Skill 的严格静态校验使用 `oil-skill-creator`：

```text
python <oil-skill-creator>/scripts/validate_skill.py <skill-path> --strict --weak-model
```

效果评测样例位于 `evals/evals.json`。当前只有作者自测；尚未完成隔离执行者与用户盲评，不能把静态校验当作审美效果证明。

# Third-party notices and prior art

This Skill was designed after reviewing open-source academic-presentation Skills. It reuses mechanisms rather than copying their task histories or fixed visual styles.

## Code adaptation

`scripts/audit_pptx.py` adapts the PPTX ZIP/XML text-extraction approach from [Knowledge Cat PPT](https://github.com/gnipbao/knowledge-cat-ppt-skill), MIT License, Copyright (c) 2026 Knowledge Cat contributors. The adapted version adds Chinese placeholder patterns, slide geometry checks, cover/navigation/closing validation, stale-term scanning, and notes/master/layout inspection.

The MIT permission notice for Knowledge Cat PPT is reproduced below:

> Permission is hereby granted, free of charge, to any person obtaining a copy
> of this software and associated documentation files (the "Software"), to deal
> in the Software without restriction, including without limitation the rights
> to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
> copies of the Software, and to permit persons to whom the Software is
> furnished to do so, subject to the following conditions:
>
> The above copyright notice and this permission notice shall be included in all
> copies or substantial portions of the Software.

## Design and workflow prior art

- [group-meeting-ppt-skill](https://github.com/Zero-stargazer/group-meeting-ppt-skill) (MIT): duration-aware evidence narrative, real paper figures, figure-source tracking, release gates.
- [Literature Report PPT Builder](https://github.com/fangyuanopus/literature-report-ppt-builder) (MIT): paper-analysis contract, template hygiene, navigation preservation, stale metadata and unused-layout cleanup.
- [scholar-slides](https://github.com/luwill/research-skills/tree/main/scholar-slides) (MIT): fidelity-first academic slides, source provenance, native PPTX parity and rendered QA.
- [academic-pptx-skill](https://github.com/Gabberflast/academic-pptx-skill) (MIT): communication-first academic structure, evidence/exhibit discipline, citations and readable typography.
- [research-paper-lifecycle-skills / make-slides](https://github.com/ShaishavMaisuria/research-paper-lifecycle-skills/tree/main/skills/make-slides) (Apache-2.0): slot-aware storyboarding, figure inventory and deterministic pacing checks.
- [PPT Master](https://github.com/hugohe3/ppt-master) (MIT): optional native editable PPTX authoring, template and repair runtime. No PPT Master code is bundled here.

No code was copied from projects whose repository did not expose a clear reuse license during review.



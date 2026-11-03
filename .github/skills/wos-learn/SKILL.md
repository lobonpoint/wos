---
name: wos-learn
description: Extract candidate lessons, decisions, patterns, precedents, and repeatable workflows from project artifacts; improve the second brain safely.
---
# WOS Learn
1. Read `AGENTS.md`. Find project ID with `python -m wos list projects`.
2. Extract evidence from an artifact *inside* the project directory: `python -m wos learn PRJ-ID projects/YYYY/folder/outputs/report.html` (also accepts `.pptx`, `.md`, `.txt`).
3. Read the generated `runtime/knowledge-candidates/KN-*.md`. Extraction is raw evidence, **not** an approved lesson or decision.
4. Review and fill: problem, alternatives, chosen option, rationale, constraints, approval evidence, observed outcome, reusable guidance, cases where guidance does *not* apply.
5. Compare to related knowledge via `python -m wos search "term"`; link sources rather than cloning content.
6. Require human confirmation before considering a candidate trusted, and never auto-promote an exception into a bank standard.
7. If a workflow appears three or more times, propose a skill spec and tests; do not silently create or enable it.
8. Summarize promoted candidates separately from still-pending suggestions.

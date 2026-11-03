---
name: wos-brief
description: Generate a concise executive work brief with top three priorities, hot spots, key area pulse, decisions, commitments, and recommended next move.
---
# WOS Brief
1. Read `AGENTS.md`. Generate baseline: `python -m wos brief`.
2. Inspect registry actions/projects and the generated report. Do not invent statuses missing from input.
3. Explain **what changed** only when supported by two dated observations; otherwise say change unknown.
4. Top 3 should favor business impact (30%), urgency (25%), unblocking leverage (20%), unique contribution (15%), strategic leverage (10%). These weights are heuristics; override for verified incidents/compliance deadlines.
5. Prioritize actions you can actually advance; identify delegates and waiting dependencies separately.
6. Output in this order: Executive snapshot; Top 3 with why-now and next move; Hot spots; Key area pulse (Salesforce Architecture, nCino, Copado/DevOps, AI SDLC, other registered initiatives); commitments/dependencies; keep top of mind; first move.
7. Cite IDs, project paths, and last-verified dates. Explicitly label stale/unknown areas.
8. Keep briefing ~2–3 minutes by default, expanding only on request. Save optional polished HTML or PPTX to the relevant project `outputs/` after reviewing data.

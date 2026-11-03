---
name: wos-project
description: Create, find, update, and close dated work project folders and registry records. Use for substantive decisions or deliverables.
---
# WOS Project
1. Read `AGENTS.md`. Find prior projects: `python -m wos list projects`.
2. If a close match exists, use its existing project ID. Do not create duplicates.
3. For new, approved substantive work: `python -m wos project-new "Short title" --objective "Expected outcome"`.
4. Add actions with `python -m wos action-add "Next action" --project PRJ-ID [--due YYYY-MM-DD]`.
5. Put materials in `inputs/`, drafts in `working/`, and final HTML/PPTX in `outputs/`. All must remain in approved storage.
6. Record *verified* decision, alternatives, rationale, evidence, approval, and outcomes in `decisions.md`; mark unconfirmed items as proposed.
7. Before closing, review unresolved actions and run `wos-learn`; do not treat generated output as approval or completion.
8. Return project ID, path, actions, deliverables, missing facts, and one next move.

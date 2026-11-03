# Operating guidance

## Daily routine
1. Review Outlook flags/search folders. Select an explicitly approved, minimal set of messages for local export.
2. Import exports with `python -m wos email-import ...`. `.msg` requires optional `extract-msg` package. `.eml` works without dependencies.
3. Review proposed actions (`python -m wos list actions`) and pending project proposals (`python -m wos list project_proposals`). Do not approve everything by default.
4. Use `wos-project` for significant new work. Keep project inputs, working notes and outputs together.
5. Run `python -m wos brief`; use Copilot `wos-brief` for a 2-minute human-readable summary and top 3 priorities.
6. Mark work done only when verified. Capture candidate knowledge through `wos-learn` after the deliverable/decision is confirmed.

## Desktop Outlook caveat
There is **no direct Outlook integration in the MVP**. Classic Outlook Windows may permit manual `.msg` Save As. Optional `extract-msg` must be approved and installed for reading `.msg`; `.eml` exports may depend on Outlook version. Do not bypass endpoint restrictions. Outlook COM integration is a later, distinct IT-reviewed enhancement, and is not portable to new Outlook or macOS.

## Data governance checklist
- Approved GitHub/public code intake and allowed open-source dependencies
- Approved AI model, Copilot agent mode and content classifications
- Approved local email export and retention handling
- Approved workspace storage, ACL, endpoint security and backups
- Repository access control, no secrets/data in commits, no syncing runtime
- Auditability, source fidelity and human approvals for consequential actions

## Known MVP limitations
- Message parsing reads plain-text bodies (not HTML-only emails or attachments).
- Keyword-based candidate detection may yield false positives and false negatives.
- It does not automatically correlate emails with existing project IDs or detect sent replies.
- Brief ranking uses manual/default rubric values, not independently verified impacts.
- Full-text search is a basic SQL LIKE search; semantic/vector search is not included.
- PPTX extraction covers slide/notes text, not charts embedded as images.
- Automated reporting for team/manager calls is deliberately not included yet.
- Local SQLite is intended for a single user, not concurrent network-share edits.

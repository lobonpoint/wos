# WOS — Work Chief of Staff (MVP)

A **public-safe, local-first template** for a GitHub Copilot-powered Work Operating System. Five Copilot skills and a Python/SQLite CLI connect dated project folders, approved local email exports, a work registry, executive briefs, and candidate Second Brain knowledge.

**This is an MVP, not a fully autonomous agent or a certified bank-compliant product.** It never connects to Outlook, sends email, accesses Graph/Power Automate, or uploads anything. Its email classification is a reviewable keyword heuristic, **not** an LLM inference engine. Copilot performs richer reasoning when you invoke the skills in an authorized workspace.

## Before using it at a bank
- Obtain employer approval to download/use public repository code on a managed device, process email in GitHub Copilot, export local mailbox files, store data locally, and use scripts. An enterprise Copilot license **does not by itself** grant mailbox-content approval.
- Use only **company-approved** storage and tools. Do not transfer confidential data to a personal machine or account.
- **Never publish real emails, projects, architecture standards, personnel details, tokens, or drafts** to this public repo, forks, GitHub issues, PRs, or logs. `.gitignore` is defense-in-depth, not a data-loss control.
- Keep bank-specific runtime state and sensitive project directories outside Git where possible. `runtime/` and `projects/` are gitignored in this template. The `examples/demo-request.eml` file is an explicitly synthetic exception to the ignore rule.
- Make no external sends, approvals, production changes, or destructive modifications without an authorized process and human review.

## Quickstart (Python 3.11+; standard library only)

```powershell
# Clone an approved copy of this code to your corporate workstation
python -m wos init
python -m wos project-new "Synthetic API security review" --objective "Demo a decision package"
python -m wos action-add "Evaluate authentication options"
python -m wos email-import examples/demo-request.eml
python -m wos list project_proposals
python -m wos list actions
python -m wos brief
```

The brief appears in `runtime/reports/YYYY-MM-DD-brief.md`. Select `wos-brief` in an approved VS Code Copilot agent session to analyze it and summarize your top three, risks, and pulse. Command invocation may vary by VS Code version: you may type `use the wos-brief skill` in Copilot Chat instead of assuming a `/wos-brief` slash command is registered.

**Approve a proposal only after review:**

```powershell
python -m wos proposal-approve PRO-XXXXXXXXXX
python -m wos list projects
```

**Status updates:**

```powershell
python -m wos action-set ACT-XXXXXXXXXX open
python -m wos action-set ACT-XXXXXXXXXX done
```

**Capture knowledge (candidate only):**

```powershell
python -m wos learn PRJ-XXXXXXXXXX projects/2026/2026-11-02-synthetic-api-security-review/outputs/assessment.html
python -m wos search "security"
```

`wos-learn` can extract text from Markdown, HTML, and PPTX files; visual diagrams and screenshots still need separate human or approved visual review. Optional `.msg` support: `python -m pip install extract-msg` **only if your bank approves installing that package**. Otherwise use approved `.eml` exports. Some Outlook installations do not support direct `.eml` export; see `docs/OPERATIONS.md`.

## The five skills

| Skill | Job |
| --- | --- |
| `wos-project` | Dated project lifecycle, actions, decisions and deliverables |
| `wos-email` | Email triage, reply drafts, candidate actions/project proposals |
| `wos-brief` | Top 3, hot spots, key area pulse, dependencies, next move |
| `wos-review` | Detailed daily/weekly review and manager/team reporting preparation |
| `wos-learn` | Candidate knowledge extraction and reusable skill proposals |

The canonical Skill instructions live in `.github/skills/wos-*/SKILL.md`. Repo-wide guardrails live in `AGENTS.md`.

## How the pieces work

1. **Sources**: selected approved `.eml`/`.msg` files and project artifacts.
2. **Registry**: local `runtime/work.db` holds projects, sources, actions, proposed new projects, decisions, knowledge candidates, and an audit event log.
3. **Projects**: `projects/YYYY/YYYY-MM-DD-slug/` contains `project.md`, `decisions.md`, `inputs/`, `working/`, `outputs/`.
4. **Briefing**: deterministic baseline reports; Copilot adds interpretation but must cite record IDs and avoid invented status.
5. **Second Brain**: candidate extracts from prior HTML/PPTX/Markdown artifacts, pending review before becoming trusted guidance.

## What is intentionally deferred

- Fully automated email-to-project classification and existing-thread matching
- Scheduled Outlook capture, sending messages, creating Outlook drafts
- Automatic team reminders or collection of replies
- Biweekly manager report delivery, peer management meeting integration
- Vector search, multi-agent runtime, dashboards, enterprise integrations

These can be added as new `wos-*` skills **after** reliability, compliance, and data freshness are proven. See `docs/ROADMAP.md`.

## Testing

```bash
python -m unittest discover -s tests -v
```

No network, proprietary files, or third-party dependencies are needed to run the included tests.

## License
MIT. The source is a reusable template; organizational use must comply with your employer's policies.

## WOS Convert — Office/PDF/HTML to Markdown

Use the new `wos-convert` skill for token-efficient retrieval and searchable local Markdown. Converts `.docx`, `.pptx`, `.xlsx`, `.pdf`, `.html`, `.htm`, `.md`, and `.txt` into `runtime/converted/<name>.md` (gitignored). It does **not** call an external service, render slides, interpret charts, OCR scanned PDFs, or evaluate spreadsheet formulas.

```powershell
python -m wos convert "path/to/approved-document.docx"
python -m wos convert "path/to/deck.pptx" --max-chars 80000
python -m wos convert "path/to/workbook.xlsx" --max-rows 500 --max-columns 30
python -m wos convert "path/to/report.pdf"
python -m wos convert "path/to/page.html" --output "runtime/converted/page.md"
```

PDF requires `PyMuPDF`, which must be approved before installation: `python -m pip install pymupdf`. For Office documents, only modern `.docx`, `.pptx`, `.xlsx` formats are supported; convert legacy `.doc`, `.ppt`, `.xls` using approved workplace tooling first. Long output is **explicitly truncated** at 40,000 characters by default and prints warnings: use `--max-chars` when you need comprehensive coverage. Spreadsheet extraction limits rows/columns and reads stored values and formula text only. Converted Markdown is derived workplace data and must **not** be published in the public repo.

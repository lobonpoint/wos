"""Evidence-linked deterministic briefs; Copilot may improve prose but not invent evidence."""
from __future__ import annotations
from pathlib import Path
import datetime as dt
from .core import now

def priority_score(r):
    return round((r['impact']*30+r['urgency']*25+r['unblock']*20+
                  r['unique_value']*15+r['strategic']*10)/5,1)

def generate_brief(root, con, output=None):
    today=dt.date.today().isoformat()
    active=[dict(r) for r in con.execute("SELECT * FROM actions WHERE status IN ('open','proposed','blocked')")]
    eligible=sorted(active,key=lambda r:(r['status']=='blocked',priority_score(r)),reverse=True)
    projects=[dict(r) for r in con.execute("SELECT * FROM projects WHERE status='active' ORDER BY created_at DESC")]
    blocked=[r for r in eligible if r['status']=='blocked']
    waiting=[dict(r) for r in con.execute("SELECT * FROM actions WHERE status='waiting'")]
    overdue=[r for r in active if r['due_date'] and r['due_date']<today]
    proposals=con.execute("SELECT COUNT(*) FROM project_proposals WHERE status='pending'").fetchone()[0]
    lines=[f'# Executive Work Brief — {today}','',
           '> Generated from local registry only. Proposed tasks and scores require human verification.',
           '',f'**Snapshot:** {len(projects)} active projects · {len(active)} proposed/open/blocked actions · '
           f'{len(blocked)} blocked · {len(waiting)} waiting · {proposals} proposed projects.','',
           '## Top 3 priorities']
    if not eligible: lines.append('- No actionable work recorded; coverage may be incomplete.')
    for i,r in enumerate(eligible[:3],1):
        lines += [f'{i}. **{r["title"]}** [{r["id"]}] — {r["status"]}, heuristic score {priority_score(r)}/100.',
                  f'   - Next step: Verify context and decide the action. Source: {r["source_id"] or "manual entry"}; project: {r["project_id"] or "unassigned"}.']
    lines+=['','## Hot spots']
    if not blocked and not overdue: lines.append('- No recorded blockers or overdue actions; not evidence of overall health.')
    for r in blocked: lines.append(f'- Blocked: {r["title"]} [{r["id"]}]')
    for r in overdue: lines.append(f'- Overdue: {r["title"]} [{r["id"]}], due {r["due_date"]}')
    lines+=['','## Key area pulse']
    if not projects: lines.append('- No active projects registered.')
    for p in projects[:20]:
        count=con.execute("SELECT COUNT(*) FROM actions WHERE project_id=? AND status NOT IN ('done','cancelled')",(p['id'],)).fetchone()[0]
        lines.append(f'- **{p["title"]}** [{p["id"]}]: {p["status"]}; {count} unresolved recorded actions. Last verified update: unknown.')
    lines+=['','## Commitments & dependencies']
    for r in waiting[:15]: lines.append(f'- Waiting: {r["title"]} [{r["id"]}]')
    if not waiting: lines.append('- No waiting items recorded.')
    lines+=['','## Keep top of mind',f'- {proposals} project proposals need review.',
            '- Validate missing/stale input sources before treating this as complete.','',
            '## Recommended first move']
    lines.append(f'- Review **{eligible[0]["title"]}** and confirm its priority and next action.' if eligible else '- Import approved inputs or capture your highest-value active work.')
    lines+=['',f'_Generated {now()} UTC_','']
    content='\n'.join(lines)
    dest=Path(output) if output else Path(root)/'runtime'/'reports'/f'{today}-brief.md'
    dest.parent.mkdir(parents=True,exist_ok=True)
    dest.write_text(content,encoding='utf-8')
    return dest

def generate_review(root,con):
    return generate_brief(root,con,Path(root)/'runtime'/'reports'/(dt.date.today().isoformat()+'-review.md'))

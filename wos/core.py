"""WOS local registry and safe project lifecycle. Standard library only."""
from __future__ import annotations
import datetime as dt
import json
import os
import re
import sqlite3
import uuid
from pathlib import Path

SCHEMA = '''
PRAGMA foreign_keys=ON;
CREATE TABLE IF NOT EXISTS projects(id TEXT PRIMARY KEY, slug TEXT NOT NULL, title TEXT NOT NULL,
 created_at TEXT NOT NULL, status TEXT NOT NULL DEFAULT 'active', objective TEXT NOT NULL DEFAULT '', path TEXT NOT NULL UNIQUE);
CREATE TABLE IF NOT EXISTS sources(id TEXT PRIMARY KEY, kind TEXT NOT NULL, external_id TEXT NOT NULL,
 subject TEXT NOT NULL, source_date TEXT, sender TEXT, body TEXT NOT NULL DEFAULT '',
 path TEXT, imported_at TEXT NOT NULL, UNIQUE(kind,external_id));
CREATE TABLE IF NOT EXISTS actions(id TEXT PRIMARY KEY, project_id TEXT REFERENCES projects(id),
 title TEXT NOT NULL, owner TEXT NOT NULL DEFAULT '', due_date TEXT, status TEXT NOT NULL DEFAULT 'proposed',
 impact INTEGER NOT NULL DEFAULT 3, urgency INTEGER NOT NULL DEFAULT 3, unblock INTEGER NOT NULL DEFAULT 3,
 unique_value INTEGER NOT NULL DEFAULT 3, strategic INTEGER NOT NULL DEFAULT 3,
 source_id TEXT REFERENCES sources(id), notes TEXT NOT NULL DEFAULT '', created_at TEXT NOT NULL, updated_at TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS project_proposals(id TEXT PRIMARY KEY, source_id TEXT REFERENCES sources(id),
 title TEXT NOT NULL, rationale TEXT NOT NULL DEFAULT '', status TEXT NOT NULL DEFAULT 'pending',
 project_id TEXT REFERENCES projects(id), created_at TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS decisions(id TEXT PRIMARY KEY, project_id TEXT REFERENCES projects(id),
 title TEXT NOT NULL, rationale TEXT NOT NULL DEFAULT '', status TEXT NOT NULL DEFAULT 'proposed',
 source_id TEXT REFERENCES sources(id), updated_at TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS knowledge(id TEXT PRIMARY KEY, project_id TEXT REFERENCES projects(id),
 title TEXT NOT NULL, kind TEXT NOT NULL, body TEXT NOT NULL, status TEXT NOT NULL DEFAULT 'candidate',
 source_path TEXT, created_at TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS events(id INTEGER PRIMARY KEY AUTOINCREMENT, happened_at TEXT NOT NULL,
 kind TEXT NOT NULL, record_id TEXT NOT NULL, payload TEXT NOT NULL);
CREATE INDEX IF NOT EXISTS ix_actions_status ON actions(status);
CREATE INDEX IF NOT EXISTS ix_actions_project ON actions(project_id);
CREATE INDEX IF NOT EXISTS ix_sources_subject ON sources(subject);
'''

def now():
    return dt.datetime.now(dt.timezone.utc).isoformat(timespec='seconds')

def slugify(s):
    slug = re.sub(r'[^a-z0-9]+', '-', s.lower()).strip('-')
    return slug[:60] or 'untitled'

def connect(root: Path):
    root = Path(root).resolve()
    (root/'runtime').mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(root/'runtime'/'work.db')
    con.row_factory = sqlite3.Row
    con.executescript(SCHEMA)
    return con

def event(con, kind, rid, data):
    con.execute('INSERT INTO events(happened_at,kind,record_id,payload) VALUES(?,?,?,?)',
                (now(), kind, rid, json.dumps(data, sort_keys=True)))

def create_project(root, con, title, objective='', created=None):
    created = created or dt.date.today().isoformat()
    dt.date.fromisoformat(created)
    base = f'{created}-{slugify(title)}'
    folder = Path(root)/'projects'/created[:4]/base
    suffix = 2
    while folder.exists():
        folder = Path(root)/'projects'/created[:4]/f'{base}-{suffix}'
        suffix += 1
    pid = 'PRJ-' + uuid.uuid4().hex[:10].upper()
    folder.mkdir(parents=True)
    for name in ('inputs','working','outputs'):
        (folder/name).mkdir()
    meta = f'''---\nid: {pid}\ntitle: {json.dumps(title)}\ncreated: {created}\nstatus: active\n---\n\n# {title}\n\n## Objective\n{objective or 'To be defined.'}\n\n## Scope and stakeholders\nTo be confirmed.\n\n## Actions and dependencies\nSee the WOS registry.\n\n## Deliverables\nStore HTML, PPTX, and other outputs in outputs/.\n'''
    (folder/'project.md').write_text(meta, encoding='utf-8')
    (folder/'decisions.md').write_text('# Decisions\n\nNo verified decisions yet.\n',encoding='utf-8')
    with con:
        con.execute('INSERT INTO projects(id,slug,title,created_at,objective,path) VALUES(?,?,?,?,?,?)',
                    (pid,slugify(title),title,created,objective,str(folder.relative_to(root))))
        event(con,'project_created',pid,{'title':title})
    return {'id':pid,'path':str(folder),'title':title}

def add_action(con, title, project_id=None, owner='', due_date=None, status='proposed',
               source_id=None, notes='', scores=None):
    if due_date:
        dt.date.fromisoformat(due_date)
    if status not in {'proposed','open','blocked','waiting','done','cancelled'}:
        raise ValueError('Invalid action status')
    scores = scores or {}
    vals = [int(scores.get(x,3)) for x in ('impact','urgency','unblock','unique_value','strategic')]
    if not all(1 <= x <= 5 for x in vals):
        raise ValueError('Scores must be 1..5')
    aid='ACT-'+uuid.uuid4().hex[:10].upper()
    with con:
        con.execute('''INSERT INTO actions(id,project_id,title,owner,due_date,status,impact,urgency,unblock,
          unique_value,strategic,source_id,notes,created_at,updated_at) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)''',
          (aid,project_id,title,owner,due_date,status,*vals,source_id,notes,now(),now()))
        event(con,'action_created',aid,{'status':status,'title':title})
    return aid

def update_action(con, aid, status):
    if status not in {'proposed','open','blocked','waiting','done','cancelled'}:
        raise ValueError('Invalid status')
    with con:
        cur=con.execute('UPDATE actions SET status=?, updated_at=? WHERE id=?',(status,now(),aid))
        if not cur.rowcount: raise ValueError(f'Unknown action: {aid}')
        event(con,'action_updated',aid,{'status':status})

def approve_proposal(root, con, proposal_id):
    prop=con.execute('SELECT * FROM project_proposals WHERE id=?',(proposal_id,)).fetchone()
    if not prop or prop['status']!='pending':
        raise ValueError('Proposal not found or already processed')
    prj=create_project(root,con,prop['title'],prop['rationale'])
    with con:
        con.execute("UPDATE project_proposals SET status='approved',project_id=? WHERE id=?",(prj['id'],proposal_id))
        event(con,'proposal_approved',proposal_id,{'project_id':prj['id']})
    return prj

def list_rows(con, table, limit=100):
    if table not in {'projects','actions','sources','project_proposals','decisions','knowledge','events'}:
        raise ValueError('Invalid table')
    return [dict(r) for r in con.execute(f'SELECT * FROM {table} LIMIT ?',(limit,))]

"""Read approved local email exports. Never connects to Outlook, networks or sends mail."""
from __future__ import annotations
import email
from email import policy
from email.parser import BytesParser
import hashlib
from pathlib import Path
import re
import uuid
from .core import now, event

KEYWORDS = ('review','approve','approval','assessment','design','decision','proposal','architecture','exception','deliverable')
ACTION_PHRASES = ('please ', 'could you', 'can you', 'need your', 'action required', 'by friday', 'by monday', 'review', 'approve')

def message_body(msg):
    if msg.is_multipart():
        for part in msg.walk():
            if part.get_content_type()=='text/plain' and part.get_content_disposition()!='attachment':
                try: return part.get_content()
                except Exception: pass
        return ''
    return msg.get_content() if msg.get_content_type()=='text/plain' else ''

def parse_local(path):
    path=Path(path)
    if path.suffix.lower()=='.eml':
        raw=path.read_bytes()
        msg=BytesParser(policy=policy.default).parsebytes(raw)
        identifier=str(msg.get('Message-ID','')).strip() or hashlib.sha256(raw).hexdigest()
        return {'external_id':identifier,'subject':str(msg.get('Subject','(No subject)')),
                'sender':str(msg.get('From','')),'date':str(msg.get('Date','')),
                'body':message_body(msg)[:100000]}
    if path.suffix.lower()=='.msg':
        try: import extract_msg
        except ImportError as exc:
            raise RuntimeError('.msg requires optional package extract-msg; alternatively export .eml') from exc
        m=extract_msg.Message(str(path))
        try:
            raw=path.read_bytes()
            return {'external_id':str(m.messageId or '').strip() or hashlib.sha256(raw).hexdigest(),
                    'subject':m.subject or '(No subject)', 'sender':m.sender or '',
                    'date':str(m.date or ''), 'body':(m.body or '')[:100000]}
        finally:
            m.close()
    raise ValueError('Only .eml or .msg exports are supported')

def clean_subject(text):
    return re.sub(r'^(?:(?:re|fw|fwd)\s*:\s*)+', '', text, flags=re.I).strip()

def import_messages(root, con, files):
    stats={'imported':0,'duplicates':0,'proposals':0,'actions':0,'errors':[]}
    from .core import add_action
    for f in files:
        p=Path(f)
        try:
            m=parse_local(p)
            if con.execute('SELECT 1 FROM sources WHERE kind=? AND external_id=?',('email',m['external_id'])).fetchone():
                stats['duplicates']+=1; continue
            sid='SRC-'+uuid.uuid4().hex[:10].upper()
            subject=clean_subject(m['subject'])
            text=(subject+' '+m['body']).lower()
            with con:
                con.execute('''INSERT INTO sources(id,kind,external_id,subject,source_date,sender,body,path,imported_at)
                  VALUES(?,?,?,?,?,?,?,?,?)''',(sid,'email',m['external_id'],m['subject'],m['date'],m['sender'],m['body'],str(p.resolve()),now()))
                event(con,'email_imported',sid,{'subject':m['subject']})
            stats['imported']+=1
            # Heuristic candidates only. Never assert an email contains a verified task or approval.
            if any(k in text for k in ACTION_PHRASES):
                add_action(con,'Review email: '+subject[:160],source_id=sid,
                           notes='Automatically proposed from email; verify request, ownership and due date.',status='proposed')
                stats['actions']+=1
            if any(k in subject.lower() for k in KEYWORDS):
                matches=con.execute('SELECT id,title FROM projects').fetchall()
                if not any(subject.lower() in r['title'].lower() or r['title'].lower() in subject.lower() for r in matches):
                    pid='PRO-'+uuid.uuid4().hex[:10].upper()
                    with con:
                        con.execute('''INSERT INTO project_proposals(id,source_id,title,rationale,created_at)
                          VALUES(?,?,?,?,?)''',(pid,sid,subject[:160],
                          'Potential substantive work from email subject; review before approval.',now()))
                        event(con,'project_proposed',pid,{'source_id':sid})
                    stats['proposals']+=1
        except Exception as exc:
            stats['errors'].append({'file':str(p),'error':str(exc)})
    return stats

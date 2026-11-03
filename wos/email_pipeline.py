"""Local, manually-triggered processing of approved email drop folder."""
from __future__ import annotations
from datetime import datetime, timezone
from pathlib import Path
import json
import shutil
from .email import import_messages

FOLDERS = ('intake', 'processed', 'failed', 'drafts', 'reports')

def ensure_email_dirs(root):
    base = Path(root) / 'email'
    for folder in FOLDERS:
        (base / folder).mkdir(parents=True, exist_ok=True)
    return base

def _move_without_clobber(source, destination_dir):
    destination_dir.mkdir(parents=True, exist_ok=True)
    dest = destination_dir / source.name
    index = 2
    while dest.exists():
        dest = destination_dir / f'{source.stem}-{index}{source.suffix}'
        index += 1
    return shutil.move(str(source), str(dest))

def process_intake(root, con):
    base = ensure_email_dirs(root)
    items = sorted(f for f in (base / 'intake').iterdir() if f.is_file() and f.suffix.lower() in {'.msg','.eml'})
    summary = {'scanned':len(items),'imported':0,'duplicates':0,'actions':0,'proposals':0,'failed':0,'files':[]}
    for item in items:
        result = import_messages(root, con, [item])
        for field in ('imported','duplicates','actions','proposals'):
            summary[field] += result[field]
        ok = not result['errors']
        destination = 'processed' if ok else 'failed'
        moved = _move_without_clobber(item, base / destination)
        if not ok:
            summary['failed'] += 1
        summary['files'].append({'filename':item.name,'status':'duplicate' if result['duplicates'] else destination,
                                 'saved_as':Path(moved).name, 'errors':result['errors']})
    timestamp=datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
    report=base/'reports'/f'import-{timestamp}.json'
    report.write_text(json.dumps(summary,indent=2,ensure_ascii=False),encoding='utf-8')
    summary['report']=str(report)
    return summary

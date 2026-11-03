from __future__ import annotations
import argparse
import json
from pathlib import Path
from .core import connect, create_project, add_action, update_action, approve_proposal, list_rows
from .email import import_messages
from .email_pipeline import ensure_email_dirs, process_intake
from .brief import generate_brief,generate_review
from .knowledge import capture,search
from .convert import convert_file

def main():
    p=argparse.ArgumentParser(prog='wos',description='Local Work Chief of Staff; no network, no sending')
    p.add_argument('--root',type=Path,default=Path.cwd(),help='Workspace root (default current directory)')
    sp=p.add_subparsers(dest='cmd',required=True)
    sp.add_parser('init'); a=sp.add_parser('project-new');a.add_argument('title');a.add_argument('--objective',default='')
    a=sp.add_parser('action-add');a.add_argument('title');a.add_argument('--project');a.add_argument('--due');a.add_argument('--owner',default='')
    a=sp.add_parser('action-set');a.add_argument('id');a.add_argument('status',choices=['proposed','open','waiting','blocked','done','cancelled'])
    a=sp.add_parser('email-import');a.add_argument('files',nargs='+',type=Path)
    sp.add_parser('email-process')
    a=sp.add_parser('proposal-approve');a.add_argument('id')
    sp.add_parser('brief');sp.add_parser('review')
    a=sp.add_parser('list');a.add_argument('table',choices=['projects','actions','sources','project_proposals','decisions','knowledge','events'])
    a=sp.add_parser('learn');a.add_argument('project_id');a.add_argument('source_path',type=Path);a.add_argument('--title')
    a=sp.add_parser('search');a.add_argument('query')
    a=sp.add_parser('convert');a.add_argument('source',type=Path);a.add_argument('--output',type=Path);a.add_argument('--max-chars',type=int,default=40000);a.add_argument('--max-rows',type=int,default=250);a.add_argument('--max-columns',type=int,default=30);a.add_argument('--overwrite',action='store_true')
    args=p.parse_args(); root=args.root.resolve()
    con=connect(root)
    try:
        if args.cmd=='init':
            for x in ('projects','runtime/inbox','runtime/reports','runtime/drafts'):(root/x).mkdir(parents=True,exist_ok=True)
            ensure_email_dirs(root)
            result={'initialized':str(root),'database':str(root/'runtime/work.db')}
        elif args.cmd=='project-new':result=create_project(root,con,args.title,args.objective)
        elif args.cmd=='action-add':result={'id':add_action(con,args.title,args.project,args.owner,args.due)}
        elif args.cmd=='action-set':update_action(con,args.id,args.status);result={'id':args.id,'status':args.status}
        elif args.cmd=='email-import':result=import_messages(root,con,args.files)
        elif args.cmd=='email-process':result=process_intake(root,con)
        elif args.cmd=='proposal-approve':result=approve_proposal(root,con,args.id)
        elif args.cmd=='brief':result={'report':str(generate_brief(root,con))}
        elif args.cmd=='review':result={'report':str(generate_review(root,con))}
        elif args.cmd=='list':result=list_rows(con,args.table)
        elif args.cmd=='learn':result={'candidate':str(capture(root,con,args.project_id,args.source_path,args.title))}
        elif args.cmd=='search':result=search(con,args.query)
        elif args.cmd=='convert':result=convert_file(args.source,args.output or root/'runtime'/'converted'/(args.source.stem+'.md'),max_chars=args.max_chars,max_rows=args.max_rows,max_columns=args.max_columns,overwrite=args.overwrite)
        print(json.dumps(result,indent=2,ensure_ascii=False))
    finally:con.close()
if __name__=='__main__':main()

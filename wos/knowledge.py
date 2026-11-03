"""Candidate-only knowledge extraction from local artifacts. No automatic policy promotion."""
from __future__ import annotations
import html
from html.parser import HTMLParser
from pathlib import Path
import re
import uuid
import zipfile
from xml.etree import ElementTree
from .core import now,event
class Extractor(HTMLParser):
    def __init__(self): super().__init__(); self.parts=[]; self.skip=0
    def handle_starttag(self, tag, attrs):
        if tag in ('script','style'): self.skip+=1
    def handle_endtag(self,tag):
        if tag in ('script','style') and self.skip:self.skip-=1
    def handle_data(self,data):
        if not self.skip and data.strip():self.parts.append(data.strip())

def extract(path):
    path=Path(path)
    if path.suffix.lower() in ('.md','.txt'):
        return path.read_text(encoding='utf-8',errors='replace')[:200000]
    if path.suffix.lower() in ('.html','.htm'):
        p=Extractor();p.feed(path.read_text(encoding='utf-8',errors='replace'))
        return '\n'.join(p.parts)[:200000]
    if path.suffix.lower()=='.pptx':
        pieces=[]
        with zipfile.ZipFile(path) as z:
            names=sorted((n for n in z.namelist() if re.fullmatch(r'ppt/slides/slide\d+\.xml',n)),
                         key=lambda n:int(re.search(r'slide(\d+)',n).group(1)))
            names+=sorted(n for n in z.namelist() if re.fullmatch(r'ppt/notesSlides/notesSlide\d+\.xml',n))
            for n in names:
                doc=ElementTree.fromstring(z.read(n))
                terms=[(node.text or '') for node in doc.iter() if node.tag.endswith('}t')]
                pieces.append(n+'\n'+' '.join(terms))
        return '\n\n'.join(pieces)[:200000]
    raise ValueError('Supported knowledge inputs: .md .txt .html .htm .pptx')

def capture(root,con,project_id,source_path,title=None):
    project=con.execute('SELECT * FROM projects WHERE id=?',(project_id,)).fetchone()
    if not project:raise ValueError('Unknown project')
    path=Path(source_path).resolve()
    # Prevent accidental extraction of arbitrary unrelated files.
    project_dir=(Path(root)/project['path']).resolve()
    if not path.is_relative_to(project_dir):raise ValueError('Source must belong to project directory')
    body=extract(path)
    if not body.strip():raise ValueError('Artifact has no extractable text; inspect image content manually')
    kid='KN-'+uuid.uuid4().hex[:10].upper()
    summary=f'''# Candidate knowledge: {title or path.stem}\n\nStatus: CANDIDATE — requires human validation.\nProject: {project_id}\nSource: {path.relative_to(root)}\n\n## Extracted evidence (not a verified decision)\n\n{body[:12000]}\n\n## Human review required\n- Actual decision and rationale:\n- Applicable standards and scope:\n- Evidence of approval:\n- Outcome and exceptions:\n- Reusability and limitations:\n'''
    out=Path(root)/'runtime'/'knowledge-candidates'/f'{kid}.md'
    out.parent.mkdir(parents=True,exist_ok=True)
    out.write_text(summary,encoding='utf-8')
    with con:
        con.execute('INSERT INTO knowledge(id,project_id,title,kind,body,status,source_path,created_at) VALUES(?,?,?,?,?,?,?,?)',
                    (kid,project_id,title or path.stem,'extraction',summary,'candidate',str(path.relative_to(root)),now()))
        event(con,'knowledge_candidate',kid,{'project_id':project_id})
    return out

def search(con,query):
    q='%'+query.lower()+'%'
    return [dict(r) for r in con.execute('''SELECT id,project_id,title,kind,status,source_path FROM knowledge
      WHERE lower(title) LIKE ? OR lower(body) LIKE ? LIMIT 30''',(q,q))]

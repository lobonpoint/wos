"""Offline, conservative, citation-friendly conversion of approved Office/PDF/HTML to Markdown.
No network, no macros, no external programs. XLSX uses read-only OOXML, not spreadsheet evaluation.
"""
from __future__ import annotations
import html
from html.parser import HTMLParser
from pathlib import Path
import re
from xml.etree import ElementTree as ET
from zipfile import ZipFile

SUPPORTED={'.md','.txt','.html','.htm','.docx','.pptx','.xlsx','.pdf'}
W='http://schemas.openxmlformats.org/wordprocessingml/2006/main'
A='http://schemas.openxmlformats.org/drawingml/2006/main'
S='http://schemas.openxmlformats.org/spreadsheetml/2006/main'

def clean(s):
    return re.sub(r'[ \t]+',' ',str(s or '')).strip()

def cell(s):
    return clean(s).replace('|','\\|').replace('\n',' / ')

def table(rows):
    if not rows:return ''
    width=max(len(r) for r in rows)
    rows=[list(r)+['']*(width-len(r)) for r in rows]
    return '\n'.join(['| '+' | '.join(cell(x) for x in rows[0])+' |',
                      '| '+' | '.join('---' for _ in range(width))+' |']+
                     ['| '+' | '.join(cell(x) for x in r)+' |' for r in rows[1:]])

class HTMLToMD(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True);self.out=[];self.skip=0;self.list_depth=0;self.row=[];self.rows=[];self.in_cell=False;self.captured=[]
    def handle_starttag(self,t,attrs):
        if t in ('script','style','svg','noscript'):self.skip+=1;return
        if self.skip:return
        if re.fullmatch(r'h[1-6]',t):self.out.append('\n\n'+'#'*int(t[1])+' ')
        elif t in ('p','div','section','article','blockquote'):self.out.append('\n')
        elif t=='br':self.out.append('\n')
        elif t in ('ul','ol'):self.list_depth+=1;self.out.append('\n')
        elif t=='li':self.out.append('\n'+'  '*max(0,self.list_depth-1)+'- ')
        elif t=='tr':self.row=[]
        elif t in ('td','th'):self.in_cell=True;self.captured=[]
        elif t=='table':self.rows=[]
    def handle_data(self,data):
        if self.skip:return
        if self.in_cell:self.captured.append(data)
        else:self.out.append(data)
    def handle_endtag(self,t):
        if t in ('script','style','svg','noscript'):
            self.skip=max(0,self.skip-1);return
        if self.skip:return
        if t in ('td','th'):
            self.row.append(' '.join(self.captured));self.in_cell=False
        elif t=='tr' and self.row:self.rows.append(self.row)
        elif t=='table' and self.rows:self.out.append('\n\n'+table(self.rows)+'\n\n')
        elif t in ('ul','ol'):self.list_depth=max(0,self.list_depth-1)
        elif re.fullmatch(r'h[1-6]',t):self.out.append('\n')

def normalize(txt):
    txt=html.unescape(txt).replace('\r','')
    txt=re.sub(r'\n[ \t]*\n(?:[ \t]*\n)+','\n\n',txt)
    return txt.strip()+'\n'

def docx(path):
    with ZipFile(path) as z:
        root=ET.fromstring(z.read('word/document.xml'))
    body=root.find(f'{{{W}}}body');out=[]
    for el in body:
        if el.tag==f'{{{W}}}p':
            text=''.join((e.text or '') if e.tag==f'{{{W}}}t' else '\t' if e.tag==f'{{{W}}}tab' else '\n' if e.tag==f'{{{W}}}br' else '' for e in el.iter())
            if not text.strip():continue
            sty=el.find(f'{{{W}}}pPr/{{{W}}}pStyle');style=sty.get(f'{{{W}}}val','') if sty is not None else ''
            m=re.search(r'heading([1-6])',style,re.I)
            out.append(('#'*int(m.group(1))+' ' if m else '')+text)
        elif el.tag==f'{{{W}}}tbl':
            rows=[]
            for tr in el.findall(f'{{{W}}}tr'):
                rows.append([' '.join(t.text or '' for t in tc.iter(f'{{{W}}}t')) for tc in tr.findall(f'{{{W}}}tc')])
            if rows:out.append(table(rows))
    return '\n\n'.join(out),[]

def pptx(path):
    out=[];warnings=[]
    with ZipFile(path) as z:
        names=sorted((n for n in z.namelist() if re.fullmatch(r'ppt/slides/slide\d+\.xml',n)),key=lambda n:int(re.search(r'slide(\d+)',n).group(1)))
        for name in names:
            num=int(re.search(r'slide(\d+)',name).group(1));root=ET.fromstring(z.read(name))
            lines=[' '.join((node.text or '') for node in paragraph.iter(f'{{{A}}}t')) for paragraph in root.iter(f'{{{A}}}p')]
            lines=[clean(x) for x in lines if clean(x)]
            out.append(f'## Slide {num}\n\n'+'\n\n'.join(lines or ['[No extractable slide text]']))
            notes=f'ppt/notesSlides/notesSlide{num}.xml'
            if notes in z.namelist():
                nroot=ET.fromstring(z.read(notes));parts=[clean(' '.join(t.text or '' for t in p.iter(f'{{{A}}}t'))) for p in nroot.iter(f'{{{A}}}p')]
                parts=[p for p in parts if p and p!=str(num)]
                if parts:out.append(f'### Speaker notes — slide {num}\n\n'+'\n'.join(parts))
    warnings.append('Slide diagrams, charts, images, and precise spatial relationships may not be represented.')
    return '\n\n'.join(out),warnings

def xlsx(path,max_rows=250,max_columns=30):
    out=[];warnings=[]
    with ZipFile(path) as z:
        shared=[]
        if 'xl/sharedStrings.xml' in z.namelist():
            root=ET.fromstring(z.read('xl/sharedStrings.xml'))
            shared=[''.join(t.text or '' for t in si.iter(f'{{{S}}}t')) for si in root.findall(f'{{{S}}}si')]
        worksheets=sorted((n for n in z.namelist() if re.fullmatch(r'xl/worksheets/sheet\d+\.xml',n)),key=lambda x:int(re.search(r'sheet(\d+)',x).group(1)))
        # Map workbook sheet labels to targets through OOXML relationships; otherwise use sheet number.
        rels={}
        relfile='xl/_rels/workbook.xml.rels'
        if relfile in z.namelist():
            for r in ET.fromstring(z.read(relfile)):
                rels[r.get('Id')]=r.get('Target','')
        titles={}
        if 'xl/workbook.xml' in z.namelist():
            root=ET.fromstring(z.read('xl/workbook.xml'))
            for sheet in root.iter(f'{{{S}}}sheet'):
                rid=sheet.get('{http://schemas.openxmlformats.org/officeDocument/2006/relationships}id')
                target=rels.get(rid,'').lstrip('/')
                if target.startswith('xl/'):name=target
                else:name='xl/'+target
                titles[name]=sheet.get('name')
        for file in worksheets:
            label=titles.get(file,Path(file).stem)
            root=ET.fromstring(z.read(file));records=[]
            for row in root.iter(f'{{{S}}}row'):
                if len(records)>=max_rows:
                    warnings.append(f'{label}: row limit ({max_rows}) reached; use --max-rows to expand.');break
                cells={}
                for c in row.findall(f'{{{S}}}c'):
                    match=re.match(r'([A-Z]+)',c.get('r',''))
                    if not match:continue
                    index=0
                    for char in match.group(1):index=index*26+ord(char)-64
                    if index>max_columns:continue
                    value=c.find(f'{{{S}}}v');formula=c.find(f'{{{S}}}f');inline=c.find(f'{{{S}}}is')
                    val=value.text if value is not None else ''
                    if c.get('t')=='s' and val:
                        try:val=shared[int(val)]
                        except (ValueError,IndexError):val='[invalid shared string]'
                    elif c.get('t')=='inlineStr' and inline is not None:
                        val=''.join(t.text or '' for t in inline.iter(f'{{{S}}}t'))
                    if formula is not None:
                        val=f'{val} [formula: ={formula.text or ""}]' if val else f'={formula.text or ""} [not calculated]'
                    cells[index]=val
                if cells:
                    width=min(max(cells),max_columns);records.append([cells.get(i,'') for i in range(1,width+1)])
            out.append(f'## Sheet: {label}\n\n'+(table(records) if records else '[No extractable cells]'))
        warnings.append('XLSX values are read from stored cells; formulas are not recalculated. Formatting, charts, merged cells, hidden rows, and images are not reproduced.')
    return '\n\n'.join(out),warnings

def pdf(path):
    try:import fitz
    except ImportError as ex:raise RuntimeError('PDF conversion requires the approved optional package PyMuPDF (pip install pymupdf).') from ex
    out=[];warnings=[]
    with fitz.open(path) as doc:
        for i,p in enumerate(doc):
            t=p.get_text('text').strip()
            out.append(f'## Page {i+1}\n\n'+(t if t else '[No extractable text — page may be scanned]'))
            if not t:warnings.append(f'Page {i+1}: no text; OCR not attempted.')
    warnings.append('PDF layout, scanned images, embedded charts, and tables may require manual visual verification.')
    return '\n\n'.join(out),warnings

def convert_file(source:Path,destination:Path|None=None,*,max_chars=40000,max_rows=250,max_columns=30,overwrite=False):
    source=Path(source).expanduser().resolve()
    if not source.is_file():raise FileNotFoundError(source)
    if source.suffix.lower() not in SUPPORTED:raise ValueError(f'Unsupported: {source.suffix}. Supported: {sorted(SUPPORTED)}')
    if max_chars<1000:raise ValueError('max_chars must be >= 1000')
    if not 1<=max_columns<=100 or not 1<=max_rows<=5000:raise ValueError('Invalid spreadsheet limits')
    if destination is None:destination=Path.cwd()/'runtime'/'converted'/f'{source.stem}.md'
    destination=Path(destination).expanduser().resolve()
    if destination==source:raise ValueError('Cannot overwrite the source')
    if destination.exists() and not overwrite:raise FileExistsError(f'{destination} exists; use --overwrite to replace')
    suffix=source.suffix.lower()
    if suffix in ('.md','.txt'):body,warnings=source.read_text(encoding='utf-8',errors='replace'),[]
    elif suffix in ('.html','.htm'):
        p=HTMLToMD();p.feed(source.read_text(encoding='utf-8',errors='replace'));body,warnings=''.join(p.out),['Interactive widgets, scripts, CSS, and images are not captured.']
    elif suffix=='.docx':body,warnings=docx(source)
    elif suffix=='.pptx':body,warnings=pptx(source)
    elif suffix=='.xlsx':body,warnings=xlsx(source,max_rows,max_columns)
    elif suffix=='.pdf':body,warnings=pdf(source)
    body=normalize(body)
    original_length=len(body)
    if original_length>max_chars:
        body=body[:max_chars].rsplit('\n',1)[0]+'\n\n[TRUNCATED: source exceeds configured limit. Re-run with --max-chars for more.]\n'
        warnings.append(f'Content truncated from {original_length} to ~{max_chars} characters; incomplete for comprehensive analysis.')
    header=f'# {source.name} — extracted text\n\n> Conversion for search and AI context; not an authoritative visual rendering. Original: `{source.name}`.\n\n'
    if warnings:header+='> **Limitations:** '+' '.join(warnings)+'\n\n'
    destination.parent.mkdir(parents=True,exist_ok=True)
    destination.write_text(header+body,encoding='utf-8')
    return {'source':str(source),'output':str(destination),'characters':len(body),'warnings':warnings}

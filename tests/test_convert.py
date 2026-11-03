import tempfile, unittest
from pathlib import Path
from zipfile import ZipFile
from wos.convert import convert_file

class ConvertTests(unittest.TestCase):
    def setUp(self):self.tmp=tempfile.TemporaryDirectory();self.root=Path(self.tmp.name)
    def tearDown(self):self.tmp.cleanup()
    def convert(self,name):return convert_file(self.root/name,self.root/(name+'.md'))
    def test_html_and_existing_output(self):
        (self.root/'a.html').write_text('<h1>Decision</h1><p>Approved for review</p><script>IGNORE</script><table><tr><th>A</th><th>B</th></tr><tr><td>One</td><td>Two</td></tr></table>')
        d=self.convert('a.html');body=Path(d['output']).read_text()
        self.assertIn('# Decision',body);self.assertIn('| One | Two |',body);self.assertNotIn('IGNORE',body)
        with self.assertRaises(FileExistsError):self.convert('a.html')
    def test_docx(self):
        with ZipFile(self.root/'a.docx','w') as z:z.writestr('word/document.xml','<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"><w:body><w:p><w:pPr><w:pStyle w:val="Heading1"/></w:pPr><w:r><w:t>My Heading</w:t></w:r></w:p><w:tbl><w:tr><w:tc><w:p><w:r><w:t>Header</w:t></w:r></w:p></w:tc></w:tr></w:tbl></w:body></w:document>')
        d=self.convert('a.docx');body=Path(d['output']).read_text();self.assertIn('# My Heading',body);self.assertIn('Header',body)
    def test_pptx(self):
        with ZipFile(self.root/'a.pptx','w') as z:z.writestr('ppt/slides/slide1.xml','<p:sld xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main" xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main"><a:p><a:r><a:t>Recommendation</a:t></a:r></a:p></p:sld>')
        d=self.convert('a.pptx');self.assertIn('## Slide 1',Path(d['output']).read_text());self.assertIn('Recommendation',Path(d['output']).read_text())
    def test_xlsx(self):
        with ZipFile(self.root/'a.xlsx','w') as z:
            z.writestr('xl/worksheets/sheet1.xml','<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main"><sheetData><row r="1"><c r="A1" t="inlineStr"><is><t>Owner</t></is></c><c r="B1" t="inlineStr"><is><t>Score</t></is></c></row><row r="2"><c r="A2" t="inlineStr"><is><t>DevOps</t></is></c><c r="B2"><f>1+1</f><v>2</v></c></row></sheetData></worksheet>')
        d=self.convert('a.xlsx');body=Path(d['output']).read_text();self.assertIn('DevOps',body);self.assertIn('[formula: =1+1]',body)
    def test_limits(self):
        (self.root/'big.txt').write_text('long content\n'*500)
        d=convert_file(self.root/'big.txt',self.root/'out.md',max_chars=1000)
        self.assertIn('TRUNCATED',Path(d['output']).read_text())
        self.assertTrue(d['warnings'])
    def test_unsupported(self):
        (self.root/'a.xls').write_bytes(b'demo')
        with self.assertRaises(ValueError):self.convert('a.xls')

if __name__=='__main__':unittest.main()

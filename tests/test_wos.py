import tempfile
import unittest
from pathlib import Path
from wos.core import connect,create_project,add_action,update_action,approve_proposal
from wos.email import import_messages
from wos.brief import generate_brief
from wos.knowledge import capture,search

class WorkOSTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.root=Path(self.tmp.name)
        self.con=connect(self.root)
    def tearDown(self):self.con.close();self.tmp.cleanup()
    def test_project_and_actions(self):
        p=create_project(self.root,self.con,'Demo NFR Review',created='2026-11-02')
        self.assertTrue((Path(p['path'])/'project.md').exists())
        self.assertTrue((Path(p['path'])/'outputs').exists())
        a=add_action(self.con,'Review requirements',project_id=p['id'],scores={'impact':5})
        update_action(self.con,a,'open')
        self.assertEqual(self.con.execute('SELECT status FROM actions WHERE id=?',(a,)).fetchone()[0],'open')
    def test_email_idempotence_and_proposals(self):
        f=self.root/'demo.eml'
        f.write_text('From: a@example.invalid\nSubject: API Security Review\nMessage-ID: <unique@example.invalid>\nContent-Type: text/plain; charset=utf-8\n\nPlease review this architecture.\n')
        a=import_messages(self.root,self.con,[f,f])
        self.assertEqual((a['imported'],a['duplicates'],a['proposals'],a['actions']),(1,1,1,1))
        proposal=self.con.execute('SELECT id FROM project_proposals').fetchone()[0]
        p=approve_proposal(self.root,self.con,proposal)
        self.assertTrue(Path(p['path']).exists())
        with self.assertRaises(ValueError): approve_proposal(self.root,self.con,proposal)
    def test_brief_and_knowledge(self):
        p=create_project(self.root,self.con,'Demo Project')
        a=add_action(self.con,'Handle high priority matter',project_id=p['id'],status='blocked',scores={'impact':5,'urgency':5})
        report=generate_brief(self.root,self.con)
        self.assertIn('Handle high priority matter',report.read_text())
        html=Path(p['path'])/'outputs'/'decision.html'
        html.write_text('<h1>API approach</h1><script>bad()</script><p>Chosen after review</p>')
        candidate=capture(self.root,self.con,p['id'],html)
        self.assertIn('Chosen after review',candidate.read_text())
        self.assertNotIn('bad()',candidate.read_text())
        self.assertEqual(len(search(self.con,'API approach')),1)
        with self.assertRaises(ValueError):capture(self.root,self.con,p['id'],self.root/'outside.html')
    def test_no_synthetic_completed_work(self):
        p=create_project(self.root,self.con,'No actions')
        report=generate_brief(self.root,self.con).read_text()
        self.assertIn('No actionable work recorded',report)

if __name__=='__main__':unittest.main()

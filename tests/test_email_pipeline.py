import tempfile
import unittest
from pathlib import Path
from wos.core import connect
from wos.email_pipeline import ensure_email_dirs,process_intake

SAMPLE=b'''From: Person <person@example.test>\nTo: Manager <manager@example.test>\nMessage-ID: <sample-flow@example.test>\nSubject: Request architecture review\nDate: Mon, 2 Nov 2026 12:00:00 -0500\nContent-Type: text/plain; charset=utf-8\n\nCould you review the integration design by Friday?\n'''
class EmailPipelineTests(unittest.TestCase):
 def test_batch_moves_and_deduplicates(self):
  with tempfile.TemporaryDirectory() as tmp:
   root=Path(tmp); folders=ensure_email_dirs(root)
   (folders/'intake'/'one.eml').write_bytes(SAMPLE)
   (folders/'intake'/'bad.eml').write_bytes(b'') # parsed as empty message; still valid in email parser
   (folders/'intake'/'skip.txt').write_text('ignore')
   db=connect(root)
   try:
    out=process_intake(root,db)
    self.assertEqual(out['scanned'],2)
    self.assertEqual(out['imported'],2)
    self.assertEqual(out['actions'],1)
    self.assertEqual(out['proposals'],1)
    self.assertTrue((folders/'processed'/'one.eml').exists())
    self.assertTrue((folders/'intake'/'skip.txt').exists())
    self.assertTrue(Path(out['report']).exists())
    (folders/'intake'/'two.eml').write_bytes(SAMPLE)
    next_out=process_intake(root,db)
    self.assertEqual(next_out['duplicates'],1)
    self.assertEqual(next_out['actions'],0)
   finally:db.close()
 def test_failed_extension_moves_to_failed(self):
  with tempfile.TemporaryDirectory() as tmp:
   root=Path(tmp); folders=ensure_email_dirs(root)
   (folders/'intake'/'broken.msg').write_bytes(b'not a message')
   db=connect(root)
   try:
    result=process_intake(root,db)
    self.assertEqual(result['failed'],1)
    self.assertTrue((folders/'failed'/'broken.msg').exists())
   finally:db.close()
if __name__=='__main__':unittest.main()

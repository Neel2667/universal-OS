from __future__ import annotations
import json, sys, tempfile, unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'core')); sys.path.insert(0,str(ROOT/'tools'))
from universal_core.mirrors import MirrorEndpoint, fetch_from_mirrors
from run_fault_matrix import run
class NextFiveTests(unittest.TestCase):
 def test_file_mirror_fallback_and_http_rejection(self):
  with tempfile.TemporaryDirectory() as d:
   root=Path(d); (root/'good').mkdir(); (root/'good'/'metadata.json').write_bytes(b'ok')
   result=fetch_from_mirrors([MirrorEndpoint((root/'missing').as_uri(),1),MirrorEndpoint((root/'good').as_uri(),2)],'metadata.json',max_bytes=10,allow_file_for_test=True)
   self.assertEqual(result.data,b'ok')
   with self.assertRaises(Exception): MirrorEndpoint('http://example.test').normalized()
 def test_fault_matrix(self):
  output=run(); self.assertEqual(output['healthy-first-boot'],'committed'); self.assertEqual(output['failed-health'],'rolled-back')
if __name__=='__main__': unittest.main()

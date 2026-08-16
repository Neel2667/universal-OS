from __future__ import annotations
import json,sys,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'tools'))
from validate_device_matrix import MatrixError,validate as matrix
from validate_build_lock import validate as lock
class Gates(unittest.TestCase):
 def test_lab_matrix_and_build_lock(self):
  matrix(json.loads((ROOT/'testdata/device-enablement/synthetic-orion-lab-matrix.json').read_text()))
  lock(json.loads((ROOT/'testdata/build/reference-lock.json').read_text()))
 def test_verified_requires_recovery_update_rollback(self):
  raw=json.loads((ROOT/'testdata/device-enablement/synthetic-orion-lab-matrix.json').read_text())
  with self.assertRaises(MatrixError):matrix(raw,'verified')
if __name__=='__main__':unittest.main()

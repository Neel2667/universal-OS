from __future__ import annotations
import json,sys,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'core'));sys.path.insert(0,str(ROOT/'tools'))
from universal_core.adapter import BootstrapAdapter,SanitizedBootObservation,discovery_from_adapter
from universal_core.errors import ContractError,ResolutionError
from validate_recovery_proof import validate
class AdapterRecovery(unittest.TestCase):
 def test_adapter_derives_safe_discovery(self):
  a=BootstrapAdapter.from_dict(json.loads((ROOT/'testdata/bootstrap-adapter/synthetic-orion.json').read_text())); d=discovery_from_adapter(a,SanitizedBootObservation.from_dict({'product_id':'synthetic-orion','unlocked':True,'active_slot':'a','slot_count':2}));self.assertEqual(d.board_family,'synthetic-orion')
 def test_adapter_rejects_sensitive_or_wrong_layout(self):
  with self.assertRaises(ContractError): SanitizedBootObservation.from_dict({'product_id':'x','unlocked':True,'slot_count':2,'serial':'no'})
  a=BootstrapAdapter.from_dict(json.loads((ROOT/'testdata/bootstrap-adapter/synthetic-orion.json').read_text()))
  with self.assertRaises(ResolutionError): discovery_from_adapter(a,SanitizedBootObservation.from_dict({'product_id':'synthetic-orion','unlocked':True,'slot_count':1}))
 def test_recovery_fixture_validates(self): validate(json.loads((ROOT/'testdata/recovery/synthetic-orion-recovered.json').read_text()))
if __name__=='__main__':unittest.main()

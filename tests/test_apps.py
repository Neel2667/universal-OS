from __future__ import annotations
import json,sys,unittest
from datetime import datetime,timedelta,timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'core'))
from universal_core.apps import AppAdmissionPolicy,AppManifest
from universal_core.errors import ContractError,TrustError
NOW=datetime(2026,8,16,tzinfo=timezone.utc)
class Apps(unittest.TestCase):
 def manifest(self):return AppManifest.from_dict(json.loads((ROOT/'testdata/app/example-wasi-app.json').read_text()))
 def test_wasi_app_requires_signed_package_and_scoped_grant(self):
  app=self.manifest();p=AppAdmissionPolicy()
  with self.assertRaises(TrustError):p.admit(app,package_signed=False,system_signer=False)
  p.admit(app,package_signed=True,system_signer=False)
  grant=p.grant(app,'uos.app.files.read-selected',NOW,NOW+timedelta(minutes=5),True)
  self.assertTrue(grant.valid_for(app.app_id,'uos.app.files.read-selected',NOW))
  with self.assertRaises(TrustError):p.grant(app,'uos.app.camera.capture',NOW,NOW+timedelta(minutes=5),True)
 def test_manifest_rejects_system_or_private_capabilities(self):
  raw=json.loads((ROOT/'testdata/app/example-wasi-app.json').read_text());raw['requested_capabilities'].append('uos.update.request-first-boot')
  with self.assertRaises(ContractError):AppManifest.from_dict(raw)
  native={**json.loads((ROOT/'testdata/app/example-wasi-app.json').read_text()),'runtime':'native-system'}
  with self.assertRaises(TrustError):AppAdmissionPolicy().admit(AppManifest.from_dict(native),package_signed=True,system_signer=False)
if __name__=='__main__':unittest.main()

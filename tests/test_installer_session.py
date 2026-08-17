from __future__ import annotations
import json,sys,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'core'))
from universal_core.adapter import BootstrapAdapter,SanitizedBootObservation
from universal_core.errors import ResolutionError
from universal_core.installer_session import DATA_LOSS_ACK,InstallerSession
class Session(unittest.TestCase):
 def session(self):
  a=BootstrapAdapter.from_dict(json.loads((ROOT/'testdata/bootstrap-adapter/synthetic-orion.json').read_text()));o=SanitizedBootObservation.from_dict(json.loads((ROOT/'testdata/installer/synthetic-orion-observation.json').read_text()));return InstallerSession.create('uos.installer.test-v1',a,o)
 def test_dry_run_redacts_observation_and_requires_ack(self):
  s=self.session();plan=s.dry_run();self.assertFalse(plan['data_loss_acknowledged']);self.assertNotIn('active_slot',str(plan));
  with self.assertRaises(ResolutionError):s.authorize_bootstrap_transfer()
  self.assertEqual(s.acknowledge_data_loss(DATA_LOSS_ACK).dry_run()['next_step'],'transfer-bootstrap-capsule')
 def test_wrong_ack_rejected(self):
  with self.assertRaises(ResolutionError):self.session().acknowledge_data_loss('yes')
if __name__=='__main__':unittest.main()

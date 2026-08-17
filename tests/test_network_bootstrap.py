from __future__ import annotations
import json,sys,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'core'))
from universal_core.errors import ContractError
from universal_core.network import NetworkBootstrap,NetworkState,ProvisioningRequest
class Network(unittest.TestCase):
 def test_usb_and_offline_do_not_need_network_credentials(self):
  n=NetworkBootstrap();self.assertEqual(n.request(ProvisioningRequest.from_dict({'schema_version':1,'method':'usb-host-transfer','credential_ref':None,'user_approved':False})).state,NetworkState.USB);self.assertFalse(n.can_fetch_mirror())
 def test_wifi_needs_user_approval_and_captive_portal_blocks_fetch(self):
  r=ProvisioningRequest.from_dict(json.loads((ROOT/'testdata/network/wifi-request.json').read_text()));n=NetworkBootstrap();self.assertEqual(n.request(r).state,NetworkState.WIFI_CONNECTING);self.assertEqual(n.wifi_result(connected=False,captive_portal=True).state,NetworkState.CAPTIVE);self.assertFalse(n.can_fetch_mirror())
 def test_plaintext_or_unapproved_wifi_rejected_or_blocked(self):
  with self.assertRaises(ContractError):ProvisioningRequest.from_dict({'schema_version':1,'method':'wifi','credential_ref':None,'user_approved':True})
  n=NetworkBootstrap();self.assertEqual(n.request(ProvisioningRequest('wifi','vault:ref',False)).state,NetworkState.WIFI_SETUP)
if __name__=='__main__':unittest.main()

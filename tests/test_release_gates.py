from __future__ import annotations
import sys,unittest
from datetime import datetime,timedelta,timezone
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
ROOT='core';sys.path.insert(0,ROOT)
from universal_core.attestation import HealthAttestation,HealthAttestationVerifier
from universal_core.audit import AuditEvent,verify_chain
from universal_core.errors import PersistenceError
NOW=datetime(2026,8,16,tzinfo=timezone.utc)
class Gates(unittest.TestCase):
 def test_signed_health_and_audit_chain(self):
  key=Ed25519PrivateKey.generate(); a=HealthAttestation.sign('p','b','u',{'core':'ready'},'health',key,NOW,NOW+timedelta(minutes=1)); self.assertTrue(HealthAttestationVerifier({'health':key.public_key()}).verify(a,profile_id='p',boot_target='b',update_id='u',now=NOW))
  first=AuditEvent.create(1,'p','staged','ok',''); second=AuditEvent.create(2,'p','committed','ok',first.event_hash); verify_chain([first,second])
  with self.assertRaises(PersistenceError): verify_chain([second,first])
 def test_bad_health_does_not_verify(self):
  key=Ed25519PrivateKey.generate(); a=HealthAttestation.sign('p','b','u',{'core':'failed'},'health',key,NOW,NOW+timedelta(minutes=1)); self.assertFalse(HealthAttestationVerifier({'health':key.public_key()}).verify(a,profile_id='p',boot_target='b',update_id='u',now=NOW))
if __name__=='__main__':unittest.main()

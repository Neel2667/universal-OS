from __future__ import annotations
import base64,json
from dataclasses import dataclass,replace
from datetime import datetime,timezone
from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey,Ed25519PublicKey
from .errors import TrustError

def _canon(v:dict)->bytes:return json.dumps(v,sort_keys=True,separators=(',',':')).encode()
@dataclass(frozen=True)
class HealthAttestation:
 profile_id:str; boot_target:str; update_id:str; issued_at:datetime; expires_at:datetime; services:dict[str,str]; key_id:str; signature:bytes
 def body(self)->dict:
  return {'profile_id':self.profile_id,'boot_target':self.boot_target,'update_id':self.update_id,'issued_at':self.issued_at.astimezone(timezone.utc).isoformat().replace('+00:00','Z'),'expires_at':self.expires_at.astimezone(timezone.utc).isoformat().replace('+00:00','Z'),'services':self.services}
 @classmethod
 def sign(cls,profile_id:str,boot_target:str,update_id:str,services:dict[str,str],key_id:str,key:Ed25519PrivateKey,issued:datetime,expires:datetime)->'HealthAttestation':
  item=cls(profile_id,boot_target,update_id,issued,expires,dict(services),key_id,b''); return replace(item,signature=key.sign(_canon(item.body())))
 def to_dict(self)->dict:
  d=self.body(); d.update({'key_id':self.key_id,'signature':base64.b64encode(self.signature).decode()}); return d
class HealthAttestationVerifier:
 def __init__(self,keys:dict[str,Ed25519PublicKey]):self.keys=dict(keys)
 def verify(self,a:HealthAttestation,*,profile_id:str,boot_target:str,update_id:str,now:datetime)->bool:
  if a.profile_id!=profile_id or a.boot_target!=boot_target or a.update_id!=update_id or a.expires_at<=now.astimezone(timezone.utc) or a.issued_at>now.astimezone(timezone.utc): return False
  key=self.keys.get(a.key_id)
  if key is None:return False
  try:key.verify(a.signature,_canon(a.body()))
  except InvalidSignature:return False
  return all(v=='ready' for v in a.services.values())

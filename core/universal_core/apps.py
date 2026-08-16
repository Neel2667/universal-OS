from __future__ import annotations
import re
from dataclasses import dataclass
from datetime import datetime,timezone
from typing import Any,Mapping
from .errors import ContractError,TrustError
APP_CAPABILITIES=frozenset({'uos.app.files.read-selected','uos.app.files.write-user-approved','uos.app.camera.capture','uos.app.microphone.record','uos.app.location.read','uos.app.network.connect','uos.app.notifications.post','uos.app.share.export'})
@dataclass(frozen=True)
class AppManifest:
 app_id:str;version:str;runtime:str;entry:str;requested_capabilities:frozenset[str]
 @classmethod
 def from_dict(cls,r:Mapping[str,Any])->'AppManifest':
  req={'schema_version','app_id','version','runtime','entry','requested_capabilities'}
  if set(r)!=req or r.get('schema_version')!=1:raise ContractError('invalid app manifest envelope')
  if not isinstance(r['app_id'],str) or not re.fullmatch(r'uos\.app\.[a-z0-9][a-z0-9._-]*',r['app_id']):raise ContractError('invalid app id')
  if not isinstance(r['version'],str) or not re.fullmatch(r'[0-9]+\.[0-9]+\.[0-9]+',r['version']):raise ContractError('invalid app version')
  if r['runtime'] not in {'wasi-component','native-system'} or not isinstance(r['entry'],str) or not r['entry']:raise ContractError('invalid app runtime/entry')
  caps=r['requested_capabilities']
  if not isinstance(caps,list) or not set(caps)<=APP_CAPABILITIES or len(set(caps))!=len(caps):raise ContractError('invalid app capabilities')
  return cls(r['app_id'],r['version'],r['runtime'],r['entry'],frozenset(caps))
@dataclass(frozen=True)
class CapabilityGrant:
 app_id:str; capability:str; issued_at:datetime; expires_at:datetime; one_shot:bool
 def valid_for(self,app_id:str,capability:str,now:datetime)->bool:
  return self.app_id==app_id and self.capability==capability and self.issued_at<=now.astimezone(timezone.utc)<self.expires_at and capability in APP_CAPABILITIES
class AppAdmissionPolicy:
 def admit(self,manifest:AppManifest,*,package_signed:bool,system_signer:bool)->None:
  if not package_signed:raise TrustError('app package is not bound to verified signed targets metadata')
  if manifest.runtime=='native-system' and not system_signer:raise TrustError('native-system runtime is reserved for trusted system packages')
  if manifest.runtime=='wasi-component' and system_signer: return
 def grant(self,manifest:AppManifest,capability:str,issued:datetime,expires:datetime,one_shot:bool)->CapabilityGrant:
  if capability not in manifest.requested_capabilities:raise TrustError('app did not request capability')
  if expires<=issued:raise ContractError('capability grant expiry must follow issue time')
  return CapabilityGrant(manifest.app_id,capability,issued,expires,one_shot)

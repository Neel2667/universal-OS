from __future__ import annotations
from dataclasses import dataclass
from enum import Enum
from typing import Any,Mapping
from .errors import ContractError,ResolutionError
class NetworkState(str,Enum):
 OFFLINE='offline';USB='usb-host-transfer';BUNDLE='offline-bundle';WIFI_SETUP='wifi-setup-required';WIFI_CONNECTING='wifi-connecting';WIFI_CONNECTED='wifi-connected';CAPTIVE='captive-portal';ETHERNET='ethernet';CELLULAR='cellular';FAILED='failed'
@dataclass(frozen=True)
class ProvisioningRequest:
 method:str;credential_ref:str|None;user_approved:bool
 @classmethod
 def from_dict(cls,r:Mapping[str,Any])->'ProvisioningRequest':
  if set(r)!={'schema_version','method','credential_ref','user_approved'} or r.get('schema_version')!=1:raise ContractError('invalid provisioning envelope')
  if r['method'] not in {'usb-host-transfer','offline-bundle','wifi','ethernet','cellular','bluetooth-tether'} or not isinstance(r['user_approved'],bool) or not (isinstance(r['credential_ref'],str) or r['credential_ref'] is None):raise ContractError('invalid provisioning request')
  if r['method']=='wifi' and not r['credential_ref']:raise ContractError('wifi request needs opaque credential reference')
  return cls(r['method'],r['credential_ref'],r['user_approved'])
@dataclass(frozen=True)
class NetworkStatus:
 state:NetworkState;method:str|None;message:str
class NetworkBootstrap:
 def __init__(self):self.status=NetworkStatus(NetworkState.OFFLINE,None,'offline-safe; no network selected')
 def request(self,r:ProvisioningRequest)->NetworkStatus:
  if r.method in {'usb-host-transfer','offline-bundle'}:
   self.status=NetworkStatus(NetworkState.USB if r.method=='usb-host-transfer' else NetworkState.BUNDLE,r.method,'local artifact path selected');return self.status
  if not r.user_approved:
   self.status=NetworkStatus(NetworkState.WIFI_SETUP if r.method=='wifi' else NetworkState.FAILED,r.method,'explicit user approval required');return self.status
  if r.method=='wifi':self.status=NetworkStatus(NetworkState.WIFI_CONNECTING,'wifi','using opaque locally protected credential reference');return self.status
  if r.method=='ethernet':self.status=NetworkStatus(NetworkState.ETHERNET,'ethernet','local ethernet link selected');return self.status
  if r.method=='cellular':self.status=NetworkStatus(NetworkState.FAILED,'cellular','cellular bootstrap unavailable until verified device radio support exists');return self.status
  self.status=NetworkStatus(NetworkState.FAILED,r.method,'transport not available in v0.1');return self.status
 def wifi_result(self,*,connected:bool,captive_portal:bool=False)->NetworkStatus:
  if self.status.state!=NetworkState.WIFI_CONNECTING:raise ResolutionError('wifi result without active wifi provisioning')
  if captive_portal:self.status=NetworkStatus(NetworkState.CAPTIVE,'wifi','captive portal requires visible user resolution; no artifact fetch')
  elif connected:self.status=NetworkStatus(NetworkState.WIFI_CONNECTED,'wifi','network transport available; signed metadata still required')
  else:self.status=NetworkStatus(NetworkState.FAILED,'wifi','wifi connection failed; use USB or offline bundle')
  return self.status
 def can_fetch_mirror(self)->bool:return self.status.state in {NetworkState.WIFI_CONNECTED,NetworkState.ETHERNET}

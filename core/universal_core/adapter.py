from __future__ import annotations
from dataclasses import dataclass
from typing import Any,Mapping
from .discovery import DiscoveryRecord
from .errors import ContractError,ResolutionError
@dataclass(frozen=True)
class BootstrapAdapter:
 adapter_id:str; product_ids:frozenset[str]; architecture:str; board_family:str; soc_family:str; partition_model:str; transport:str; factory_restore_documented:bool
 @classmethod
 def from_dict(cls,r:Mapping[str,Any])->'BootstrapAdapter':
  req={'schema_version','adapter_id','match','transport','recovery'}
  if set(r)!=req or r.get('schema_version')!=1: raise ContractError('invalid bootstrap adapter manifest')
  m=r['match']; rec=r['recovery']
  if not isinstance(m,dict) or set(m)!={'product_ids','architecture','board_family','soc_family','partition_model'}: raise ContractError('invalid adapter match')
  products=m['product_ids']
  if not isinstance(products,list) or not products or any(not isinstance(x,str) or not x or x=='*' for x in products): raise ContractError('invalid adapter product ids')
  if m['architecture'] not in {'arm64','armv7','x86_64','riscv64'} or m['partition_model'] not in {'ab','transactional','single-slot'}: raise ContractError('invalid adapter platform')
  if not isinstance(rec,dict) or set(rec)!={'offline_path_required','factory_restore_documented'} or rec['offline_path_required'] is not True or not isinstance(rec['factory_restore_documented'],bool): raise ContractError('invalid adapter recovery policy')
  if r['transport'] not in {'fastboot','recovery','adb'}: raise ContractError('invalid adapter transport')
  return cls(r['adapter_id'],frozenset(products),m['architecture'],m['board_family'],m['soc_family'],m['partition_model'],r['transport'],rec['factory_restore_documented'])
@dataclass(frozen=True)
class SanitizedBootObservation:
 product_id:str; unlocked:bool; active_slot:str|None; slot_count:int
 @classmethod
 def from_dict(cls,r:Mapping[str,Any])->'SanitizedBootObservation':
  allowed={'product_id','unlocked','active_slot','slot_count'}
  if set(r)-allowed or not {'product_id','unlocked','slot_count'}<=set(r): raise ContractError('boot observation has unknown/missing fields')
  if not isinstance(r['product_id'],str) or not r['product_id'] or not isinstance(r['unlocked'],bool) or not isinstance(r['slot_count'],int) or r['slot_count']<1: raise ContractError('invalid boot observation')
  slot=r.get('active_slot')
  if slot is not None and slot not in {'a','b'}: raise ContractError('invalid active slot')
  return cls(r['product_id'],r['unlocked'],slot,r['slot_count'])
def discovery_from_adapter(adapter:BootstrapAdapter,obs:SanitizedBootObservation)->DiscoveryRecord:
 if obs.product_id not in adapter.product_ids: raise ResolutionError('boot observation product does not match approved adapter')
 if not obs.unlocked: raise ResolutionError('bootloader is not confirmed unlocked')
 expected_slots=2 if adapter.partition_model=='ab' else 1
 if obs.slot_count!=expected_slots: raise ResolutionError('boot observation slot layout does not match adapter')
 return DiscoveryRecord.from_dict({'schema_version':1,'record_id':'uos.discovery.adapter-derived-v1','architecture':adapter.architecture,'hardware':{'board_family':adapter.board_family,'soc_family':adapter.soc_family},'boot':{'bootloader_state':'unlocked','partition_model':adapter.partition_model},'transport':{'protocol':adapter.transport}})

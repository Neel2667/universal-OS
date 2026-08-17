#!/usr/bin/env python3
from __future__ import annotations
import json,re
from dataclasses import dataclass
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
class EnablementError(ValueError): pass
@dataclass(frozen=True)
class Enablement:
 id:str; profile_id:str; tier:str; recovery_tested:bool
 @classmethod
 def parse(cls,raw:dict)->'Enablement':
  req={'schema_version','enablement_id','profile_id','bootstrap_capsule','support_tier','recovery','features','provenance_components'}
  if set(raw)!=req or raw.get('schema_version')!=1: raise EnablementError('invalid enablement envelope')
  if not isinstance(raw['enablement_id'],str) or not re.fullmatch(r'uos\.enablement\.[a-z0-9][a-z0-9._-]*',raw['enablement_id']): raise EnablementError('invalid enablement id')
  tier=raw['support_tier']
  if tier not in {'profiled','lab','verified','maintained','retired'}: raise EnablementError('invalid support tier')
  recovery=raw['recovery']; capsule=raw['bootstrap_capsule']; features=raw['features']; prov=raw['provenance_components']
  if not isinstance(recovery,dict) or set(recovery)!={'offline_path','tested'} or not all(isinstance(x,bool) for x in recovery.values()): raise EnablementError('invalid recovery evidence')
  if not isinstance(capsule,dict) or set(capsule)!={'id','version'} or not all(isinstance(x,str) and x for x in capsule.values()): raise EnablementError('invalid bootstrap capsule')
  if not isinstance(features,dict) or not features or any(v not in {'working','partial','unavailable','untested','blocked','unsafe'} for v in features.values()): raise EnablementError('invalid feature matrix')
  if not isinstance(prov,list) or not prov or any(not isinstance(x,str) or not x.startswith('uos.') for x in prov): raise EnablementError('invalid provenance references')
  if tier in {'verified','maintained'} and (not recovery['offline_path'] or not recovery['tested']): raise EnablementError('verified/maintained tier requires tested offline recovery')
  if tier=='maintained' and any(v in {'untested','blocked','unsafe'} for v in features.values()): raise EnablementError('maintained tier has unresolved feature states')
  return cls(raw['enablement_id'],raw['profile_id'],tier,recovery['tested'])
def main()->int:
 records=[Enablement.parse(json.loads(p.read_text())) for p in sorted((ROOT/'testdata/device-enablement').glob('*.json'))]
 print('Validated '+str(len(records))+' device enablement record(s)')
 return 0
if __name__=='__main__': raise SystemExit(main())

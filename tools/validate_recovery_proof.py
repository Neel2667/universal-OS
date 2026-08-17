#!/usr/bin/env python3
from __future__ import annotations
import json,re
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def validate(r:dict)->None:
 req={'schema_version','adapter_id','profile_id','build_id','offline_restore','scenario','result','evidence'}
 if set(r)!=req or r.get('schema_version')!=1: raise ValueError('invalid recovery proof envelope')
 if r['result']!='recovered': raise ValueError('release recovery proof must report recovered')
 x=r['offline_restore']
 if not isinstance(x,dict) or set(x)!={'artifact_sha256','data_loss_disclosed'} or not re.fullmatch(r'[a-f0-9]{64}',x['artifact_sha256']) or x['data_loss_disclosed'] is not True: raise ValueError('invalid offline restore proof')
 if not all(isinstance(r[k],str) and r[k] for k in ('adapter_id','profile_id','build_id','evidence')): raise ValueError('invalid recovery proof fields')
def main()->int:
 for p in sorted((ROOT/'testdata/recovery').glob('*.json')): validate(json.loads(p.read_text()))
 print('Validated recovery proof records');return 0
if __name__=='__main__':raise SystemExit(main())

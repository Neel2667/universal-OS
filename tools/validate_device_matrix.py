#!/usr/bin/env python3
from __future__ import annotations
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
class MatrixError(ValueError):pass
def validate(r:dict,tier:str='lab')->None:
 req={'schema_version','profile_id','build_id','results'}
 if set(r)!=req or r.get('schema_version')!=1:raise MatrixError('invalid test matrix envelope')
 rows=r['results']
 if not isinstance(rows,list) or not rows:raise MatrixError('test matrix needs results')
 seen=set()
 for row in rows:
  if not isinstance(row,dict) or set(row)!={'area','result','evidence'} or row['area'] in seen:raise MatrixError('invalid/duplicate test matrix row')
  seen.add(row['area'])
  if row['result'] not in {'working','partial','unavailable','untested','blocked','unsafe'} or not isinstance(row['evidence'],str) or not row['evidence']:raise MatrixError('invalid test matrix result')
 if tier in {'verified','maintained'}:
  results={x['area']:x['result'] for x in rows}
  if any(results.get(area)!='working' for area in ('boot','recovery','update','rollback')):raise MatrixError('verified/maintained requires working boot/recovery/update/rollback evidence')
def main()->int:
 for p in sorted((ROOT/'testdata/device-enablement').glob('*matrix*.json')):validate(json.loads(p.read_text()))
 print('Validated device test matrices');return 0
if __name__=='__main__':raise SystemExit(main())

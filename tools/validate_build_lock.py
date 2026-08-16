#!/usr/bin/env python3
from __future__ import annotations
import json,re
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def valid_hash(x):return isinstance(x,str) and re.fullmatch(r'[a-f0-9]{64}',x)
def validate(r):
 req={'schema_version','build_id','source_revision','rust','yocto','target','inputs'}
 if set(r)!=req or r.get('schema_version')!=1:raise ValueError('invalid build lock envelope')
 for name in ('rust','yocto'):
  item=r[name]
  if not isinstance(item,dict) or set(item)!={'version' if name=='rust' else 'revision','sha256'} or not valid_hash(item['sha256']):raise ValueError('invalid '+name+' lock')
 if not isinstance(r['inputs'],list) or not r['inputs']:raise ValueError('build lock needs inputs')
 for item in r['inputs']:
  if not isinstance(item,dict) or set(item)!={'name','revision','sha256'} or not valid_hash(item['sha256']):raise ValueError('invalid build input')
def main():
 for p in sorted((ROOT/'testdata/build').glob('*.json')):validate(json.loads(p.read_text()))
 print('Validated build locks')
if __name__=='__main__':main()

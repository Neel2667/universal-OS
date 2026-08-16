#!/usr/bin/env python3
from __future__ import annotations
import argparse,hashlib,json
from pathlib import Path
def main()->int:
 p=argparse.ArgumentParser(description='Generate a deterministic UniversalOS release readiness manifest.')
 p.add_argument('--release-id',required=True); p.add_argument('--source-revision',required=True); p.add_argument('--profile-id',required=True); p.add_argument('--target-id',required=True); p.add_argument('--sbom',type=Path,required=True); p.add_argument('--passed',type=int,required=True); p.add_argument('--failed',type=int,required=True); p.add_argument('--provenance-state',choices=['test-only','review-pending','release-approved'],required=True); p.add_argument('--output',type=Path,required=True)
 a=p.parse_args(); data=a.sbom.read_bytes()
 if a.passed<0 or a.failed<0: p.error('test counts cannot be negative')
 manifest={'schema_version':1,'release_id':a.release_id,'source_revision':a.source_revision,'profile_id':a.profile_id,'target_id':a.target_id,'sbom_sha256':hashlib.sha256(data).hexdigest(),'test_summary':{'passed':a.passed,'failed':a.failed},'provenance_state':a.provenance_state}
 a.output.parent.mkdir(parents=True,exist_ok=True); a.output.write_text(json.dumps(manifest,sort_keys=True,indent=2)+'\n'); print('Wrote release manifest: '+str(a.output)); return 0
if __name__=='__main__': raise SystemExit(main())

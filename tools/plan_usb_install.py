#!/usr/bin/env python3
from __future__ import annotations
import argparse,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'core'))
from universal_core.adapter import BootstrapAdapter,SanitizedBootObservation
from universal_core.installer_session import DATA_LOSS_ACK,InstallerSession

def main()->int:
 p=argparse.ArgumentParser(description='Create a non-executing UniversalOS USB installer dry-run plan.')
 p.add_argument('--adapter',type=Path,required=True);p.add_argument('--observation',type=Path,required=True);p.add_argument('--session-id',default='uos.installer.dry-run-v1');p.add_argument('--acknowledge-data-loss',action='store_true')
 a=p.parse_args();session=InstallerSession.create(a.session_id,BootstrapAdapter.from_dict(json.loads(a.adapter.read_text())),SanitizedBootObservation.from_dict(json.loads(a.observation.read_text())))
 if a.acknowledge_data_loss:session=session.acknowledge_data_loss(DATA_LOSS_ACK)
 print(json.dumps(session.dry_run(),sort_keys=True,indent=2));return 0
if __name__=='__main__':raise SystemExit(main())

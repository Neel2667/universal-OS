from __future__ import annotations
from dataclasses import dataclass
from .adapter import BootstrapAdapter,SanitizedBootObservation,discovery_from_adapter
from .errors import ContractError,ResolutionError
DATA_LOSS_ACK='I UNDERSTAND THIS MAY ERASE DATA'
@dataclass(frozen=True)
class InstallerSession:
 session_id:str; adapter:BootstrapAdapter; observation:SanitizedBootObservation; data_loss_acknowledged:bool
 @classmethod
 def create(cls,session_id:str,adapter:BootstrapAdapter,observation:SanitizedBootObservation)->'InstallerSession':
  if not session_id.startswith('uos.installer.'):raise ContractError('invalid installer session id')
  discovery_from_adapter(adapter,observation)
  return cls(session_id,adapter,observation,False)
 def acknowledge_data_loss(self,phrase:str)->'InstallerSession':
  if phrase!=DATA_LOSS_ACK:raise ResolutionError('data-loss acknowledgement phrase does not match')
  return InstallerSession(self.session_id,self.adapter,self.observation,True)
 def dry_run(self)->dict:
  discovery=discovery_from_adapter(self.adapter,self.observation)
  return {'session_id':self.session_id,'adapter_id':self.adapter.adapter_id,'transport':self.adapter.transport,'profile_hint':{'architecture':discovery.architecture,'board_family':discovery.board_family,'soc_family':discovery.soc_family,'partition_model':discovery.partition_model},'data_loss_acknowledged':self.data_loss_acknowledged,'recovery_path':'documented-factory-restore' if self.adapter.factory_restore_documented else 'offline-required','next_step':'transfer-bootstrap-capsule' if self.data_loss_acknowledged else 'require-data-loss-acknowledgement'}
 def authorize_bootstrap_transfer(self)->None:
  if not self.data_loss_acknowledged:raise ResolutionError('installer cannot transfer bootstrap before explicit data-loss acknowledgement')

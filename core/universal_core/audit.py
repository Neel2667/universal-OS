from __future__ import annotations
import hashlib,json
from dataclasses import dataclass
from typing import Iterable
from .errors import PersistenceError
def _hash(v:dict)->str:return hashlib.sha256(json.dumps(v,sort_keys=True,separators=(',',':')).encode()).hexdigest()
@dataclass(frozen=True)
class AuditEvent:
 sequence:int; profile_id:str; phase:str; reason:str; previous_hash:str; event_hash:str
 @classmethod
 def create(cls,sequence:int,profile_id:str,phase:str,reason:str,previous_hash:str)->'AuditEvent':
  raw={'sequence':sequence,'profile_id':profile_id,'phase':phase,'reason':reason,'previous_hash':previous_hash}; return cls(**raw,event_hash=_hash(raw))
 def verify(self)->bool:return self.event_hash==_hash({'sequence':self.sequence,'profile_id':self.profile_id,'phase':self.phase,'reason':self.reason,'previous_hash':self.previous_hash})
def verify_chain(events:Iterable[AuditEvent])->None:
 prev=''
 for index,event in enumerate(events,1):
  if event.sequence!=index or event.previous_hash!=prev or not event.verify():raise PersistenceError('audit chain verification failed')
  prev=event.event_hash

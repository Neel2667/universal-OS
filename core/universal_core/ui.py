from __future__ import annotations
from dataclasses import dataclass
from typing import Any,Mapping
from .errors import ContractError
SURFACES=frozenset({'tasks','files','notes','media','communication','system','recovery'})
@dataclass(frozen=True)
class Workspace:
 workspace_id:str;title:str;surfaces:frozenset[str]
 @classmethod
 def from_dict(cls,r:Mapping[str,Any])->'Workspace':
  if set(r)!={'schema_version','workspace_id','title','surfaces'} or r.get('schema_version')!=1:raise ContractError('invalid workspace envelope')
  if not isinstance(r['workspace_id'],str) or not r['workspace_id'].startswith('uos.workspace.') or not isinstance(r['title'],str) or not r['title']:raise ContractError('invalid workspace identity')
  surfaces=r['surfaces']
  if not isinstance(surfaces,list) or not surfaces or not set(surfaces)<=SURFACES:raise ContractError('invalid workspace surfaces')
  return cls(r['workspace_id'],r['title'],frozenset(surfaces))
@dataclass(frozen=True)
class AccessibilityPreferences:
 text_scale:float;high_contrast:bool;reduced_motion:bool;screen_reader:bool;switch_navigation:bool
 @classmethod
 def from_dict(cls,r:Mapping[str,Any])->'AccessibilityPreferences':
  req={'schema_version','text_scale','high_contrast','reduced_motion','screen_reader','switch_navigation'}
  if set(r)!=req or r.get('schema_version')!=1:raise ContractError('invalid accessibility preferences')
  scale=r['text_scale']
  if not isinstance(scale,(float,int)) or not .8<=scale<=2.5 or not all(isinstance(r[x],bool) for x in req-{'schema_version','text_scale'}):raise ContractError('invalid accessibility preference values')
  return cls(float(scale),r['high_contrast'],r['reduced_motion'],r['screen_reader'],r['switch_navigation'])
@dataclass(frozen=True)
class ShellState:
 active_workspace:str;active_surface:str;recovery_mode:bool
class WorkspaceShell:
 def __init__(self,workspaces:Mapping[str,Workspace],active_workspace:str):
  if active_workspace not in workspaces:raise ContractError('active workspace not found')
  self.workspaces=dict(workspaces);self.state=ShellState(active_workspace,'tasks',False)
 def open_surface(self,surface:str)->ShellState:
  if self.state.recovery_mode and surface!='recovery':raise ContractError('recovery mode blocks normal surfaces')
  if surface not in self.workspaces[self.state.active_workspace].surfaces:raise ContractError('surface unavailable in active workspace')
  self.state=ShellState(self.state.active_workspace,surface,self.state.recovery_mode);return self.state
 def switch_workspace(self,workspace_id:str)->ShellState:
  if self.state.recovery_mode:raise ContractError('recovery mode blocks workspace switch')
  if workspace_id not in self.workspaces:raise ContractError('workspace not found')
  surface='tasks' if 'tasks' in self.workspaces[workspace_id].surfaces else next(iter(self.workspaces[workspace_id].surfaces))
  self.state=ShellState(workspace_id,surface,False);return self.state
 def enter_recovery(self)->ShellState:
  self.state=ShellState(self.state.active_workspace,'recovery',True);return self.state

from __future__ import annotations
import json,sys,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'core'))
from universal_core.errors import ContractError
from universal_core.ui import AccessibilityPreferences,Workspace,WorkspaceShell
class UI(unittest.TestCase):
 def workspace(self,id='uos.workspace.focus'):
  return Workspace.from_dict({'schema_version':1,'workspace_id':id,'title':'Focus','surfaces':['tasks','files','notes','system','recovery']})
 def test_workspace_shell_and_recovery_boundary(self):
  first=self.workspace();second=self.workspace('uos.workspace.travel');shell=WorkspaceShell({first.workspace_id:first,second.workspace_id:second},first.workspace_id)
  self.assertEqual(shell.open_surface('notes').active_surface,'notes');self.assertEqual(shell.switch_workspace(second.workspace_id).active_workspace,second.workspace_id);shell.enter_recovery()
  with self.assertRaises(ContractError):shell.switch_workspace(first.workspace_id)
 def test_accessibility_and_workspace_reject_invalid(self):
  prefs=AccessibilityPreferences.from_dict({'schema_version':1,'text_scale':2.0,'high_contrast':True,'reduced_motion':True,'screen_reader':True,'switch_navigation':False});self.assertTrue(prefs.reduced_motion)
  with self.assertRaises(ContractError):AccessibilityPreferences.from_dict({'schema_version':1,'text_scale':3.0,'high_contrast':True,'reduced_motion':True,'screen_reader':True,'switch_navigation':False})
if __name__=='__main__':unittest.main()

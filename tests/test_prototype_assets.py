from __future__ import annotations
from pathlib import Path
import unittest
ROOT=Path(__file__).resolve().parents[1]
class PrototypeAssets(unittest.TestCase):
 def test_shell_prototype_has_all_safety_surfaces(self):
  text=(ROOT/'prototype/index.html').read_text()
  for token in ('id="workspace"','id="update"','id="privacy"','id="recovery"','No account required','Known-good system preserved'):
   self.assertIn(token,text)
 def test_stitch_prompts_cover_required_journeys(self):
  text=(ROOT/'docs/STITCH_PROMPT_PACK.md').read_text()
  for word in ('Workspace','update','Recovery','Privacy','USB'):
   self.assertIn(word,text)
if __name__=='__main__':unittest.main()

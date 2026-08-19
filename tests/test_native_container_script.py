from __future__ import annotations
from pathlib import Path
import subprocess
import unittest
ROOT=Path(__file__).resolve().parents[1]
class NativeContainerScriptTests(unittest.TestCase):
 def test_script_is_posix_shell_and_contains_all_native_gates(self):
  script=ROOT/'tools/run_native_container.sh'
  subprocess.run(['sh','-n',str(script)],check=True)
  text=script.read_text()
  for token in ('build)', 'verify)', 'shell)', 'rust-test)', 'cargo test --workspace', 'aarch64-unknown-none'):
   self.assertIn(token,text)
if __name__=='__main__':unittest.main()

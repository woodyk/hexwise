"""Offline checks for the independent live-run evaluators; no provider calls."""
import sys,tempfile,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
from run_live_acceptance import evaluate
class Evaluators(unittest.TestCase):
 def test_complete_module_runs_independent_arithmetic_cases(self):
  valid=bytes.fromhex('0061736d0100000001070160027f7f017f030201000707010361646400000a09010700200020016a0b')
  with tempfile.TemporaryDirectory() as tmp:
   folder=Path(tmp);(folder/'candidate.wasm').write_bytes(valid)
   self.assertEqual(evaluate('wasm-add',valid,folder)['cases'],70)
   wrong=valid[:-2]+bytes([0x6b,0x0b]);(folder/'candidate.wasm').write_bytes(wrong)
   with self.assertRaises(ValueError):evaluate('wasm-add',wrong,folder)
 def test_prohibited_module_sections_fail_before_instantiation(self):
  with tempfile.TemporaryDirectory() as tmp:
   with self.assertRaisesRegex(ValueError,'prohibits'):evaluate('wasm-add',bytes.fromhex('0061736d0100000005020100'),Path(tmp))
 def test_untrusted_native_payload_is_not_executed(self):
  with tempfile.TemporaryDirectory() as tmp:
   for invalid in (b'',b'\0'*8,bytes.fromhex('00010091c0035fd6')):
    with self.assertRaises(ValueError):evaluate('arm64-add7',invalid,Path(tmp))
if __name__=='__main__':unittest.main()

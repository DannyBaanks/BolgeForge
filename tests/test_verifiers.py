"""End-to-end controls for missing inventories and masked earlier quine failures."""
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

class VerifierTests(unittest.TestCase):
    def test_missing_compressed_artifacts_fail(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / 'tools').mkdir()
            shutil.copyfile(ROOT / 'tools/test_compressed.py', root / 'tools/test_compressed.py')
            p = subprocess.run(['python3', str(root / 'tools/test_compressed.py')], capture_output=True, timeout=5)
            self.assertNotEqual(p.returncode, 0)
            self.assertNotIn(b'PASS', p.stdout)

    def test_first_broken_quine_cannot_be_masked_by_last_good_one(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / 'tools').mkdir()
            (root / 'artifacts').mkdir()
            shutil.copyfile(ROOT / 'tools/test_quines.py', root / 'tools/test_quines.py')
            (root / 'mb_ref').symlink_to(ROOT / 'mb_ref')
            for program in (ROOT / 'artifacts').glob('candidate_m*.mal'):
                shutil.copyfile(program, root / 'artifacts' / program.name)
            (root / 'artifacts/candidate_m281_53562b.mal').write_bytes(b'QC')
            p = subprocess.run(['python3', str(root / 'tools/test_quines.py')], capture_output=True, timeout=5)
            self.assertNotEqual(p.returncode, 0)
            self.assertIn(b'Quine mismatch', p.stderr)

    def test_unknown_rebuild_target_fails(self):
        p = subprocess.run(['python3', str(ROOT / 'tools/resynthesize.py'), 'missing-target'],
                           capture_output=True, timeout=10)
        self.assertNotEqual(p.returncode, 0)

if __name__ == '__main__':
    unittest.main()

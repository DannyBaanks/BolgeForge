"""A failed semantic check must never replace a previously published file."""
import contextlib
import io
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from tools.resynthesize import run_target

class PublicationTests(unittest.TestCase):
    def test_invalid_generated_candidate_leaves_published_artifact_untouched(self):
        # Generation costs tens of seconds; inject a valid HALT source that is
        # deliberately not a Cat. The validator and VM remain real.
        with tempfile.TemporaryDirectory() as directory:
            destination = Path(directory) / 'cat_compressed.mal'
            previous = b'previous publication must survive'
            destination.write_bytes(previous)
            with patch('tools.resynthesize.build_compressed_program', return_value=(b'QC', {})):
                with contextlib.redirect_stdout(io.StringIO()):
                    with self.assertRaisesRegex(RuntimeError, 'mismatch'):
                        run_target('cat', output_dir=Path(directory))
            self.assertEqual(destination.read_bytes(), previous)

if __name__ == '__main__':
    unittest.main()

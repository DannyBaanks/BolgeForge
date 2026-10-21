"""The diagnostic trace must not hide the oracle's runtime rejection."""
import contextlib
import io
import unittest
from tools.trace_tm import trace_run

class TraceTests(unittest.TestCase):
    def test_invalid_loader_is_rejected(self):
        with self.assertRaisesRegex(ValueError, 'INVALID_OPCODE'):
            with contextlib.redirect_stdout(io.StringIO()):
                trace_run(b'!!', 49)

    def test_jump_encrypts_destination_and_never_indexes_invalid_word(self):
        with self.assertRaisesRegex(ValueError, 'INVALID_ENCRYPTION'):
            with contextlib.redirect_stdout(io.StringIO()):
                trace_run(b"b'", 49)

    def test_nonprintable_pc_is_not_a_nop(self):
        with self.assertRaisesRegex(ValueError, 'NONPRINTABLE_PC'):
            with contextlib.redirect_stdout(io.StringIO()):
                trace_run(b"('", 49)

if __name__ == '__main__':
    unittest.main()

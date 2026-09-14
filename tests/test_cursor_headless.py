import os
from pathlib import Path
import subprocess
import tempfile
import time
import unittest

SCRIPT = Path(__file__).resolve().parents[1] / 'scripts/cursor-headless.sh'


class CursorHeadlessTests(unittest.TestCase):
    def invoke(self, args, status=0, delay=0):
        with tempfile.TemporaryDirectory() as directory:
            fake = Path(directory) / 'cursor-agent'
            fake.write_text('#!/bin/sh\nprintf "%s\\n" "$@"\nsleep "$FAKE_DELAY"\nexit "$FAKE_STATUS"\n')
            fake.chmod(0o755)
            env = dict(os.environ, PATH=directory + ':' + os.environ['PATH'],
                       FAKE_STATUS=str(status), FAKE_DELAY=str(delay))
            return subprocess.run(['bash', str(SCRIPT), *args], env=env,
                                  capture_output=True, text=True, timeout=5)

    def test_first_turn(self):
        result = self.invoke(['do the thing'])
        self.assertEqual(result.returncode, 0)
        self.assertEqual(result.stdout.splitlines(),
                         ['-p', '--force', '--output-format', 'json', 'do the thing'])

    def test_resume_turn(self):
        result = self.invoke(['next step', 'session-id'])
        self.assertEqual(result.returncode, 0)
        self.assertEqual(result.stdout.splitlines(),
                         ['-p', '--force', '--output-format', 'json',
                          '--resume', 'session-id', 'next step'])

    def test_failure_propagates(self):
        self.assertEqual(self.invoke(['prompt'], status=7).returncode, 7)

    def test_blocks_until_command_exits(self):
        started = time.monotonic()
        result = self.invoke(['prompt'], delay=0.2)
        self.assertEqual(result.returncode, 0)
        self.assertGreaterEqual(time.monotonic() - started, 0.2)

    def test_bad_arguments(self):
        for args in ([], [''], ['--bad'], ['prompt', 'session', 'extra'], ['prompt', '--bad']):
            with self.subTest(args=args):
                self.assertEqual(self.invoke(args).returncode, 2)


if __name__ == '__main__':
    unittest.main()

"""Regression coverage for subprocess isolation, deadlines, and cleanup."""
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

from architecture_test_processes import IsolatedProcesses, minimal_environment


class SubprocessSecurityTests(unittest.TestCase):
    def setUp(self):
        self.processes = IsolatedProcesses(self)

    def test_allowlist_and_isolated_user_directories(self):
        source = {"PATH": os.defpath, "SystemRoot": "C:\\Windows", "LANG": "C.UTF-8",
                  "OPENAI_API_KEY": "sentinel-secret", "AWS_SECRET_ACCESS_KEY": "sentinel-secret",
                  "UNRECOGNIZED_CREDENTIAL": "sentinel-secret", "HTTP_PROXY": "http://secret.invalid",
                  "PYTHONPATH": "/untrusted", "PYTHONSTARTUP": "/untrusted",
                  "NODE_OPTIONS": "--require=/untrusted", "NODE_PATH": "/untrusted",
                  "HOME": "/real-home", "USERPROFILE": "/real-home", "TMPDIR": "/real-tmp"}
        with tempfile.TemporaryDirectory() as directory:
            env = minimal_environment(directory, source)
            self.assertEqual(env["PATH"], source["PATH"])
            self.assertEqual(env["SystemRoot"], source["SystemRoot"])
            self.assertEqual(env["LANG"], source["LANG"])
            for key in source.keys() - {"PATH", "SystemRoot", "LANG", "HOME", "USERPROFILE", "TMPDIR"}:
                self.assertNotIn(key, env)
            for key in ("HOME", "USERPROFILE", "TMPDIR", "TMP", "TEMP", "APPDATA", "LOCALAPPDATA",
                        "XDG_CONFIG_HOME", "XDG_CACHE_HOME", "XDG_DATA_HOME", "XDG_RUNTIME_DIR"):
                self.assertTrue(Path(env[key]).is_dir())
                self.assertTrue(Path(env[key]).is_relative_to(Path(directory).resolve()))
            self.assertEqual(source["HOME"], "/real-home")

    def test_child_never_receives_parent_secret_or_startup_variables(self):
        with patch.dict(os.environ, {"TEST_SECRET_SENTINEL": "must-not-leak", "NODE_OPTIONS": "--bad-option",
                                     "PYTHONPATH": "/secret-path"}):
            isolated = IsolatedProcesses(self)
            result = isolated.run([sys.executable, "-c", "import os,json; print(json.dumps(dict(os.environ)))"],
                                  capture_output=True, text=True, check=True)
        actual = json.loads(result.stdout)
        for key in ("TEST_SECRET_SENTINEL", "NODE_OPTIONS", "PYTHONPATH"):
            self.assertNotIn(key, actual)
        self.assertEqual(actual["HOME"], isolated.env["HOME"])
        self.assertEqual(actual["TMPDIR"], isolated.env["TMPDIR"])

    def test_run_has_default_deadline_and_minimal_environment(self):
        with patch("architecture_test_processes.subprocess.run") as run:
            self.processes.run(["synthetic-command"])
            self.assertEqual(run.call_args.kwargs["timeout"], 30)
            self.assertIs(run.call_args.kwargs["env"], self.processes.env)

    def test_run_times_out_and_rejects_unbounded_deadlines(self):
        with self.assertRaises(subprocess.TimeoutExpired):
            self.processes.run([sys.executable, "-c", "import time; time.sleep(10)"], timeout=0.05,
                               capture_output=True)
        for timeout in (None, 0, -1, float("inf"), float("nan")):
            with self.subTest(timeout=timeout), self.assertRaises(ValueError):
                self.processes.run([sys.executable, "-c", "pass"], timeout=timeout)

    def test_parallel_child_timeout_kills_and_reaps(self):
        process = self.processes.start([sys.executable, "-c", "import time; time.sleep(10)"],
                                       stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        with self.assertRaises(subprocess.TimeoutExpired):
            self.processes.communicate(process, timeout=0.05)
        self.assertIsNotNone(process.poll())

    def test_test_cleanup_kills_children_even_before_communicate(self):
        testcase = unittest.TestCase()
        isolated = IsolatedProcesses(testcase)
        process = isolated.start([sys.executable, "-c", "import time; time.sleep(10)"],
                                 stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        testcase.doCleanups()
        self.assertIsNotNone(process.poll())
        self.assertFalse(Path(isolated.env["HOME"]).exists())

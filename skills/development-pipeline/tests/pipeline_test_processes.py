"""Isolated, bounded subprocesses for this skill's standalone test suite.

Only process-launch essentials cross the environment boundary. Credentials,
proxy configuration, Python/Node startup hooks, and the user's home do not.
Keep the equivalent helper in the other skill's tests in sync; neither skill
requires the other skill to be installed to run its tests.
"""
import math
import os
from pathlib import Path
import subprocess
import tempfile

DEFAULT_TIMEOUT = 30
_ENV_KEYS = ("PATH", "SystemRoot", "SYSTEMROOT", "WINDIR", "COMSPEC", "PATHEXT",
             "LANG", "LC_ALL", "LC_CTYPE", "TZ")


def minimal_environment(root, source=None):
    source = os.environ if source is None else source
    env = {key: source[key] for key in _ENV_KEYS if key in source}
    root = Path(root).resolve()
    for name in ("home", "tmp", "config", "cache", "data", "runtime"):
        (root / name).mkdir(parents=True, exist_ok=True, mode=0o700)
    env.update({
        "HOME": str(root / "home"), "USERPROFILE": str(root / "home"),
        "APPDATA": str(root / "config"), "LOCALAPPDATA": str(root / "data"),
        "TMPDIR": str(root / "tmp"), "TMP": str(root / "tmp"), "TEMP": str(root / "tmp"),
        "XDG_CONFIG_HOME": str(root / "config"), "XDG_CACHE_HOME": str(root / "cache"),
        "XDG_DATA_HOME": str(root / "data"), "XDG_RUNTIME_DIR": str(root / "runtime"),
        "PYTHONDONTWRITEBYTECODE": "1", "PYTHONUTF8": "1",
    })
    return env


def stop_process(process):
    if process.poll() is None:
        process.kill()
    process.communicate(timeout=DEFAULT_TIMEOUT)


class IsolatedProcesses:
    """Register cleanup immediately, including when a test fails mid-batch."""
    def __init__(self, testcase):
        directory = tempfile.TemporaryDirectory(prefix="isolated-test-process-")
        testcase.addCleanup(directory.cleanup)
        self.env = minimal_environment(directory.name)
        self.testcase = testcase

    def run(self, command, *, timeout=DEFAULT_TIMEOUT, **kwargs):
        if timeout is None or not math.isfinite(timeout) or timeout <= 0:
            raise ValueError("a positive subprocess timeout is required")
        return subprocess.run(command, env=self.env, timeout=timeout, **kwargs)

    def start(self, command, **kwargs):
        process = subprocess.Popen(command, env=self.env, **kwargs)
        self.testcase.addCleanup(stop_process, process)
        return process

    def communicate(self, process, *, timeout=DEFAULT_TIMEOUT):
        if timeout is None or not math.isfinite(timeout) or timeout <= 0:
            raise ValueError("a positive subprocess timeout is required")
        try:
            return process.communicate(timeout=timeout)
        except subprocess.TimeoutExpired:
            stop_process(process)
            raise

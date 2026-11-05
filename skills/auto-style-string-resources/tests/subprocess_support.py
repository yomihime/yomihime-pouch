"""Standalone bounded Python runner; do not forward credentials or Python hooks."""

import os
import subprocess
import sys


# Windows Python may require SystemRoot; locale and temporary directory settings
# preserve platform behavior. PATH/HOME/PYTHONPATH and arbitrary secrets are not needed.
ENV_KEYS = {"SYSTEMROOT", "WINDIR", "TEMP", "TMP", "TMPDIR", "LANG", "LC_ALL", "LC_CTYPE"}


def minimal_environment():
    env = {key: value for key, value in os.environ.items() if key.upper() in ENV_KEYS}
    env.update(PYTHONDONTWRITEBYTECODE="1", PYTHONIOENCODING="utf-8")
    return env


def run_script(script, *args, timeout=15):
    return subprocess.run(
        [sys.executable, str(script), *map(str, args)],
        check=False, text=True, capture_output=True, encoding="utf-8",
        env=minimal_environment(), timeout=timeout,
    )

"""Bounded, isolated test children. This is not part of the advisory runtime."""
import math
import os
from pathlib import Path
import subprocess
import tempfile

DEFAULT_TIMEOUT = 15
ENV_KEYS = ('SystemRoot', 'SYSTEMROOT', 'WINDIR', 'LANG', 'LC_ALL', 'LC_CTYPE', 'TZ')


def minimal_environment(root, source=None):
    source = os.environ if source is None else source
    env = {key: source[key] for key in ENV_KEYS if key in source}
    root = Path(root).resolve()
    for name in ('home', 'tmp', 'config', 'cache', 'data', 'runtime'):
        (root / name).mkdir(parents=True, exist_ok=True, mode=0o700)
    env.update({
        'PATH': os.defpath,
        'HOME': str(root / 'home'), 'USERPROFILE': str(root / 'home'),
        'APPDATA': str(root / 'config'), 'LOCALAPPDATA': str(root / 'data'),
        'TMPDIR': str(root / 'tmp'), 'TMP': str(root / 'tmp'), 'TEMP': str(root / 'tmp'),
        'XDG_CONFIG_HOME': str(root / 'config'), 'XDG_CACHE_HOME': str(root / 'cache'),
        'XDG_DATA_HOME': str(root / 'data'), 'XDG_RUNTIME_DIR': str(root / 'runtime'),
        'PYTHONDONTWRITEBYTECODE': '1', 'PYTHONUTF8': '1',
        'GIT_CONFIG_NOSYSTEM': '1', 'GIT_CONFIG_GLOBAL': os.devnull,
        'GIT_TERMINAL_PROMPT': '0', 'GIT_OPTIONAL_LOCKS': '0',
        'GIT_NO_LAZY_FETCH': '1', 'GIT_ALLOW_PROTOCOL': '',
    })
    return env


class IsolatedProcesses:
    def __init__(self, testcase):
        directory = tempfile.TemporaryDirectory(prefix='version-advisory-child-')
        testcase.addCleanup(directory.cleanup)
        self.env = minimal_environment(directory.name)

    def run(self, command, *, timeout=DEFAULT_TIMEOUT, **kwargs):
        if timeout is None or not math.isfinite(timeout) or timeout <= 0:
            raise ValueError('positive bounded subprocess timeout required')
        if not command or not Path(command[0]).is_absolute():
            raise ValueError('test executable must be resolved to an absolute path')
        # subprocess.run kills and reaps its direct child on timeout. These
        # fixtures do not launch arbitrary descendant trees or use shell=True.
        return subprocess.run(command, env=self.env, timeout=timeout, **kwargs)

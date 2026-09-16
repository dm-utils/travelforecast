"""No-op stand-in for the POSIX-only `fcntl` module, for running the test
suite on Windows (no WSL/Docker here). Real deploys run on HAOS (Linux),
which has the real module, so this file is never used outside local tests.

Only covers what homeassistant.runner actually calls: a PID-file flock
used solely for the optional --pid-file CLI flag, which the test harness
never exercises.
"""

LOCK_EX = 2
LOCK_NB = 4


def flock(fd, operation):  # noqa: ARG001 - matching the real fcntl.flock signature
    return None

"""No-op stand-in for the POSIX-only `resource` module, for running the
test suite on Windows. See fcntl.py in this directory for why.

Only covers what homeassistant.util.resource actually calls: reading and
raising the open-file-descriptor soft limit at startup, which is not
meaningful on Windows and not exercised by the test paths we use.
"""

RLIMIT_NOFILE = 7


def getrlimit(resource_id):  # noqa: ARG001
    return (2048, 2048)


def setrlimit(resource_id, limits):  # noqa: ARG001
    return None

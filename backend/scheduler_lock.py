"""Make sure only one worker process runs the background scheduler.

With gunicorn --workers N every worker imports the app. Without a guard each
one would start its own scheduler and the daily job would run N times. The
first process takes an exclusive file lock and keeps it for its lifetime; the
others see the lock is taken and skip. The OS drops the lock if the process dies.
"""
import os
import tempfile

_handle = None


def acquire_scheduler_lock(path=None):
    global _handle
    if _handle is not None:
        return True
    path = path or os.environ.get(
        "SCHEDULER_LOCK_FILE",
        os.path.join(tempfile.gettempdir(), "saverai-scheduler.lock"),
    )
    try:
        import fcntl
    except ImportError:  # Windows: single dev process, just run it
        return True
    handle = open(path, "a+")
    try:
        fcntl.flock(handle, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except OSError:
        handle.close()
        return False
    _handle = handle
    return True


def release_scheduler_lock():
    global _handle
    if _handle is not None:
        _handle.close()
        _handle = None

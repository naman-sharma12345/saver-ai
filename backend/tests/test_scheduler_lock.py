import subprocess
import sys
import textwrap

import scheduler_lock


def test_second_process_is_refused(tmp_path):
    scheduler_lock.release_scheduler_lock()
    lock = str(tmp_path / "s.lock")
    assert scheduler_lock.acquire_scheduler_lock(lock) is True
    try:
        code = textwrap.dedent(f"""
            import scheduler_lock
            print(scheduler_lock.acquire_scheduler_lock({lock!r}))
        """)
        out = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True,
                             cwd=str(__import__("pathlib").Path(__file__).parents[1]))
        assert out.stdout.strip() == "False"
    finally:
        scheduler_lock.release_scheduler_lock()


def test_lock_is_reentrant_in_same_process(tmp_path):
    scheduler_lock.release_scheduler_lock()
    lock = str(tmp_path / "s2.lock")
    assert scheduler_lock.acquire_scheduler_lock(lock)
    assert scheduler_lock.acquire_scheduler_lock(lock)
    scheduler_lock.release_scheduler_lock()

import fcntl
import time
from contextlib import contextmanager


class FileLock:
    def __init__(self, lock_file: str, timeout: float = 10.0):
        self.lock_file = lock_file
        self.timeout = timeout
        self._fd = None

    @contextmanager
    def acquire(self):
        start_time = time.time()
        self._fd = open(self.lock_file, "w")
        try:
            while True:
                try:
                    # Try to acquire an exclusive lock (non-blocking)
                    fcntl.flock(self._fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
                    break
                except IOError:
                    if time.time() - start_time > self.timeout:
                        raise TimeoutError(
                            f"Could not acquire lock on {self.lock_file} within "
                            f"{self.timeout} seconds"
                        )
                    time.sleep(0.1)

            yield
        finally:
            # Unlock and close
            if self._fd:
                fcntl.flock(self._fd, fcntl.LOCK_UN)
                self._fd.close()
                self._fd = None

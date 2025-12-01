import pytest
import time
import threading
from src.lock import FileLock

def test_lock_acquire_release(tmp_path):
    lock_file = tmp_path / "test.lock"
    lock = FileLock(str(lock_file))
    
    with lock.acquire():
        assert lock_file.exists()
        # Hold lock
        pass
    
    # Should be released
    # We can't easily check if it's released without trying to acquire it again
    
    with lock.acquire():
        pass

def test_lock_contention(tmp_path):
    lock_file = tmp_path / "contention.lock"
    lock1 = FileLock(str(lock_file), timeout=1.0)
    lock2 = FileLock(str(lock_file), timeout=1.0)
    
    # Thread 1 holds lock
    def hold_lock():
        with lock1.acquire():
            time.sleep(0.5)
            
    t = threading.Thread(target=hold_lock)
    t.start()
    
    # Give thread time to acquire
    time.sleep(0.1)
    
    # Thread 2 tries to acquire (should wait and succeed)
    start = time.time()
    with lock2.acquire():
        pass
    end = time.time()
    
    t.join()
    
    # Should have waited at least 0.4s (0.5 - 0.1)
    assert end - start >= 0.3

def test_lock_timeout(tmp_path):
    lock_file = tmp_path / "timeout.lock"
    lock1 = FileLock(str(lock_file))
    lock2 = FileLock(str(lock_file), timeout=0.2)
    
    # Thread 1 holds lock forever (longer than timeout)
    def hold_lock():
        with lock1.acquire():
            time.sleep(1.0)
            
    t = threading.Thread(target=hold_lock)
    t.start()
    
    time.sleep(0.1)
    
    # Thread 2 tries to acquire and should timeout
    with pytest.raises(TimeoutError):
        with lock2.acquire():
            pass
            
    t.join()

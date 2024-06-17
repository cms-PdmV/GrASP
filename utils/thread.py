"""
Some built-in objects adapted
for concurrency.
"""

import threading

class ThreadSafeDict(dict):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._lock = threading.RLock()

    def __setitem__(self, key, value):
        with self._lock:
            super().__setitem__(key, value)

    def __delitem__(self, key):
        with self._lock:
            super().__delitem__(key)

    def update(self, *args, **kwargs):
        with self._lock:
            super().update(*args, **kwargs)

    def clear(self):
        with self._lock:
            super().clear()

    def pop(self, key, default=None):
        with self._lock:
            return super().pop(key, default)

    def popitem(self):
        with self._lock:
            return super().popitem()

    def setdefault(self, key, default=None):
        with self._lock:
            return super().setdefault(key, default)

class ThreadSafeSet(set):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._lock = threading.RLock()

    def __enter__(self):
        self._lock.acquire()
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self._lock.release()

    def add(self, element):
        with self._lock:
            super().add(element)

    def remove(self, element):
        with self._lock:
            super().remove(element)

    def discard(self, element):
        with self._lock:
            super().discard(element)

    def pop(self):
        with self._lock:
            return super().pop()

    def clear(self):
        with self._lock:
            super().clear()

    def update(self, *args, **kwargs):
        with self._lock:
            super().update(*args, **kwargs)

    def difference_update(self, *args, **kwargs):
        with self._lock:
            super().difference_update(*args, **kwargs)

    def intersection_update(self, *args, **kwargs):
        with self._lock:
            super().intersection_update(*args, **kwargs)

    def symmetric_difference_update(self, *args, **kwargs):
        with self._lock:
            super().symmetric_difference_update(*args, **kwargs)

    def __ior__(self, other):
        with self._lock:
            super().update(other)
        return self

    def __iand__(self, other):
        with self._lock:
            super().intersection_update(other)
        return self

    def __isub__(self, other):
        with self._lock:
            super().difference_update(other)
        return self

    def __ixor__(self, other):
        with self._lock:
            super().symmetric_difference_update(other)
        return self

    def __or__(self, other):
        with self._lock:
            return ThreadSafeSet(super().__or__(other))

    def __and__(self, other):
        with self._lock:
            return ThreadSafeSet(super().__and__(other))

    def __sub__(self, other):
        with self._lock:
            return ThreadSafeSet(super().__sub__(other))

    def __xor__(self, other):
        with self._lock:
            return ThreadSafeSet(super().__xor__(other))

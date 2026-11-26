"""Single outstanding AI/Companion operation per Hub, including closed windows.

A lease is held until the worker really exits, not until the UI discards its result.
Only the UI thread starts work. The worker never touches Tk.
"""
import threading


class LocalWorker:
    def __init__(self):
        self._lease = threading.Lock()

    @property
    def busy(self):
        return self._lease.locked()

    def start(self, work, deliver=lambda _: None):
        if not self._lease.acquire(blocking=False):
            return False

        def run():
            try:
                result = work()
            finally:
                self._lease.release()
            deliver(result)

        try:
            threading.Thread(target=run, daemon=True).start()
        except Exception:
            self._lease.release()
            raise
        return True


def worker_for(hub):
    # Called only on the UI thread. The lease survives window destruction.
    if not hasattr(hub, '_local_worker'):
        hub._local_worker = LocalWorker()
    return hub._local_worker

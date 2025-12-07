# memory/background_worker.py
from threading import Thread
from queue import Queue
import traceback

_queue = Queue()

def _worker():
    while True:
        fn = _queue.get()
        try:
            fn()
        except Exception as e:
            print("🔥 BACKGROUND WORKER ERROR:", e)
            traceback.print_exc()
        _queue.task_done()

# ✅ START ONE PERMANENT WORKER THREAD ON IMPORT
Thread(target=_worker, daemon=True).start()

def run_in_background(fn):
    print("⚙️ BACKGROUND JOB QUEUED")
    _queue.put(fn)

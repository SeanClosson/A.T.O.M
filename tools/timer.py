import threading
import time

class TimerManager:
    def __init__(self):
        self.timers = {}
        self.lock = threading.Lock()

    def set_timer(self, seconds, name, callback):
        """
        Create a timer identified ONLY by its name.
        No internal UUIDs. No returning IDs. Just names.
        """

        if not isinstance(name, str):
            raise ValueError("Timer name must be a string.")

        def timer_thread():
            time.sleep(seconds)
            with self.lock:
                if name in self.timers:
                    callback(name)
                    del self.timers[name]

        thread = threading.Thread(target=timer_thread, daemon=True)

        with self.lock:
            self.timers[name] = thread

        thread.start()

    def cancel_timer(self, name):
        """Cancel using name only."""
        with self.lock:
            return self.timers.pop(name, None) is not None

    def list_timers(self):
        """Return active timer names."""
        with self.lock:
            return list(self.timers.keys())

    # Example callback
    def alert(self, name):
        print()
        print(f"[ALERT] Timer '{name}' has finished!")
        print()
        print('\n')

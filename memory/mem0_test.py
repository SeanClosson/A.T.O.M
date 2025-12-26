# memory/mem0_test.py
import asyncio
import threading
from mem0 import AsyncMemory

class Mem0Background:
    def __init__(self, mem0_config: dict):
        self.loop = asyncio.new_event_loop()
        self.thread = threading.Thread(
            target=self._run_loop,
            daemon=True
        )
        self.thread.start()

        # IMPORTANT: from_config is awaited INSIDE the loop
        future = asyncio.run_coroutine_threadsafe(
            AsyncMemory.from_config(mem0_config),
            self.loop
        )
        self.mem = future.result()  # REAL AsyncMemory instance

    def _run_loop(self):
        asyncio.set_event_loop(self.loop)
        self.loop.run_forever()

    def submit(self, coro):
        future = asyncio.run_coroutine_threadsafe(coro, self.loop)

        def _cb(f):
            try:
                f.result()
            except Exception as e:
                print("[MEM0 BACKGROUND ERROR]", repr(e))

        future.add_done_callback(_cb)

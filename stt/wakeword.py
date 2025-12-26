# wakeword.py
import sounddevice as sd
import queue
import json
import threading
from vosk import Model, KaldiRecognizer
import time

class WakeWordDetector:
    def __init__(
        self,
        model_path: str,
        wake_word: str = "atom",
        sample_rate: int = 16000
    ):
        self.model_path = model_path
        self.wake_word = wake_word.lower()
        self.sample_rate = sample_rate
        self.free_listen_until = 0

        self.model = Model(model_path)

        # ✅ Grammar-based recognizer for FAST keyword spotting
        grammar = f'["{self.wake_word}"]'
        self.recognizer = KaldiRecognizer(self.model, self.sample_rate, grammar)
        self.recognizer.SetWords(False)

        self.audio_queue = queue.Queue()
        self.running = False
        self.callback_fn = None


    # ✅ External callback setter
    def on_detect(self, callback_fn):
        self.callback_fn = callback_fn


    # ✅ Internal audio callback (non-blocking)
    def _audio_callback(self, indata, frames, time_info, status):
        if status:
            print("Wakeword audio status:", status)
        self.audio_queue.put(bytes(indata))


    # ✅ Main detection loop (run in thread)
    def _run(self):
        with sd.RawInputStream(
            samplerate=self.sample_rate,
            blocksize=8000,
            dtype="int16",
            channels=1,
            callback=self._audio_callback
        ):
            while self.running:
                try:
                    data = self.audio_queue.get(timeout=0.5)
                except queue.Empty:
                    continue

                # ✅ FREE LISTEN MODE (post-TTS)
                if time.time() < self.free_listen_until:
                    if self.callback_fn:
                        self.callback_fn()
                        self.free_listen_until = 0   # ✅ prevent retrigger spam
                    continue

                # ✅ NORMAL WAKEWORD MODE
                if self.recognizer.AcceptWaveform(data):
                    result = json.loads(self.recognizer.Result())
                    text = result.get("text", "").lower()

                    # ✅ HARD FILTER AGAINST FALSE POSITIVES
                    if text.strip() == self.wake_word:
                        if self.callback_fn:
                            print("✅ Wakeword confirmed:", text)
                            self.callback_fn()

                        # ✅ Reset recognizer so it doesn't re-trigger on echo
                        self.recognizer.Reset()




    # ✅ Public start method
    def start(self):
        if self.running:
            return

        self.running = True
        self.thread = threading.Thread(target=self._run, daemon=True)
        self.thread.start()

        print(f"🟢 Wakeword detector started for: '{self.wake_word}'")


    # ✅ Public stop method
    def stop(self):
        self.running = False
        print("🔴 Wakeword detector stopped")

    def allow_free_listen(self, seconds=30):
        self.free_listen_until = time.time() + seconds
        print(f"🎧 Free listen enabled for {seconds} seconds")


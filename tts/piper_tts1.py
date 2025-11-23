import subprocess
import threading
import numpy as np
import sounddevice as sd
from queue import Queue, Empty
import re

class TTS:
    def __init__(self, model_path="tts/en_US-lessac-medium.onnx", sample_rate=22050):
        self.model_path = model_path
        self.sample_rate = sample_rate

        # Queues
        self.text_queue = Queue()
        self.audio_queue = Queue()

        # Start background workers
        self.running = True
        threading.Thread(target=self._tts_worker, daemon=True).start()
        threading.Thread(target=self._play_worker, daemon=True).start()

        # Buffer for sentence aggregation
        self.buffer = ""

        # Sentence boundary regex
        self.boundary = re.compile(r"[.!?;:\n]")

    # -----------------------------------------------------------
    # INTERNAL: convert text → PCM using Piper
    # -----------------------------------------------------------
    def _synthesize(self, text):
        p = subprocess.Popen(
            ["piper", "--model", self.model_path, "--output_raw"],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE
        )
        raw, _ = p.communicate(text.encode("utf-8"))
        return np.frombuffer(raw, dtype=np.int16)

    # -----------------------------------------------------------
    # BACKGROUND: TTS worker (reads buffered sentences)
    # -----------------------------------------------------------
    def _tts_worker(self):
        while self.running:
            try:
                sentence = self.text_queue.get(timeout=0.1)
            except Empty:
                continue

            if sentence is None:
                break

            pcm = self._synthesize(sentence)
            self.audio_queue.put(pcm)

        self.audio_queue.put(None)

    # -----------------------------------------------------------
    # BACKGROUND: audio playback worker
    # -----------------------------------------------------------
    def _play_worker(self):
        while True:
            pcm = self.audio_queue.get()

            if pcm is None:
                sd.wait()
                break

            sd.play(pcm, samplerate=self.sample_rate)

    # -----------------------------------------------------------
    # PUBLIC: Push streaming text (this is called from LLM loop)
    # -----------------------------------------------------------
    def push_text(self, text_chunk):
        """
        Accept raw delta tokens from the LLM
        and convert them into full sentences.
        """

        if not text_chunk:
            return

        self.buffer += text_chunk

        # If a sentence boundary exists → flush one full sentence
        if self.boundary.search(self.buffer):
            sentences = re.split(r"([.!?;:\n])", self.buffer)

            # Combine pairs: ["Hello", ".", " How are", "?", " ..."]
            combined = []
            for i in range(0, len(sentences) - 1, 2):
                combined.append(sentences[i] + sentences[i+1])

            # Send complete sentences to TTS
            for s in combined:
                clean = s.strip()
                if clean:
                    self.text_queue.put(clean)

            # Keep the leftover partial sentence
            self.buffer = sentences[-1]

    # -----------------------------------------------------------
    # PUBLIC: call at the end to flush leftover text
    # -----------------------------------------------------------
    def finish(self):
        leftover = self.buffer.strip()
        if leftover:
            self.text_queue.put(leftover)

        self.buffer = ""

        self.text_queue.put(None)
        self.running = False

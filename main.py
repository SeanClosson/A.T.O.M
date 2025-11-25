# main.py

import sys
import signal
import os

def ensure_generated_folder():
    folder_name = "generated"
    if not os.path.exists(folder_name):
        os.makedirs(folder_name)

ensure_generated_folder()

USE_STT = True
USE_TTS = True

from llm import LLM
from cli import CLIStreamer
from tts.piper_tts import TTS

brain = LLM()
cli = CLIStreamer(brain)

# Optional STT
if USE_STT:
    try:
        from stt.stt import STT
        stt = STT()
    except Exception as e:
        print(f"[ERROR] Failed to initialize STT: {e}")
        stt = None
        USE_STT = False

# Optional TTS
try:
    tts = TTS()
except Exception as e:
    print(f"[ERROR] Failed to initialize TTS: {e}")
    tts = None
    USE_TTS = False


# --- Graceful Shutdown Handler -------------------------------------------------

def graceful_exit(*args):
    print("\n\n[INFO] Shutting down ATOM...")

    try:
        if USE_STT and stt:
            stt.shutdown_stt()
    except Exception as e:
        print(f"[WARN] Failed to shut down STT cleanly: {e}")

    try:
        if USE_TTS and tts:
            tts.close() if hasattr(tts, "close") else None
    except Exception as e:
        print(f"[WARN] Failed to shut down TTS cleanly: {e}")

    try:
        if hasattr(brain, "shutdown"):
            brain.shutdown()
    except Exception:
        pass

    print("[INFO] Exit complete. Goodbye.")
    sys.exit(0)

# Catch Ctrl+C globally
signal.signal(signal.SIGINT, graceful_exit)
signal.signal(signal.SIGTERM, graceful_exit)


def main():
    # --- Main Loop -----------------------------------------------------------------

    while True:
        try:
            # Get input
            if USE_STT:
                try:
                    user_input = stt.normal_stt()
                except Exception as e:
                    print(f"[ERROR] STT error: {e}")
                    continue
            else:
                user_input = input("\nYou: ")

            # Exit condition
            if user_input.lower() in ("exit", "quit", "exit."):
                graceful_exit()

            # Process LLM output
            try:
                # cli.stream_to_console(user_input)
                full_output = ''
                for delta in cli.stream_to_console(user_input):
                    # print(delta, end="", flush=True)
                    full_output += delta

                    # if USE_TTS and tts:
                    #     # tts.push_text(delta)
                # print(full_output)
                for_tts = tts.clean_for_tts(full_output)
                if USE_TTS and tts:
                        tts.text_to_wav(llm_output=for_tts)
                        tts.play_wav_nonblocking()
                
            except Exception as e:
                print(f"\n[ERROR] CLI/LLM streaming error: {e}")

            # if USE_TTS and tts:
            #     try:
            #         tts.finish()
            #     except Exception as e:
            #         print(f"[ERROR] TTS finish error: {e}")

        except KeyboardInterrupt:
            graceful_exit()
        except Exception as e:
            print(f"[UNHANDLED ERROR] {e}")

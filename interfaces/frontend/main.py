import streamlit as st
import requests
import json
import os
import json

API_URL = "http://localhost:8000/api/chat"
STREAM_URL = "http://localhost:8000/api/chat/stream"

HISTORY_FILE = "history.json"


# -------------------------------
# Load / Save Chat History
# -------------------------------
def load_history():
    if os.path.exists(HISTORY_FILE):
        try:
            with open(HISTORY_FILE, "r") as f:
                return json.load(f)
        except:
            return []
    return []


def save_history(history):
    with open(HISTORY_FILE, "w") as f:
        json.dump(history, f, indent=2)


# -------------------------------
# Stream generator for SSE
# -------------------------------
def stream_chat(message):
    url = f"{STREAM_URL}?message={message}"

    with requests.get(url, stream=True) as r:
        for line in r.iter_lines():

            if not line:
                continue

            # Convert bytes → str
            line = line.decode("utf-8")

            if line.startswith("data:"):
                data_str = line[5:].strip()
                if data_str == "[DONE]":
                    break  # End of stream
                try:
                    payload = json.loads(data_str)
                    if "error" in payload:
                        raise Exception(payload["error"])
                    yield payload.get("delta", "")
                except json.JSONDecodeError:
                    continue


# -------------------------------
# Streamlit Page Setup
# -------------------------------
st.set_page_config(page_title="ATOM", layout="wide")

st.title("🧠 ATOM Interface")


# Chat state
if "history" not in st.session_state:
    st.session_state.history = load_history()


# ======================================================
# CHAT HISTORY (RENDER ONLY ONCE)
# ======================================================
for item in st.session_state.history:
    st.chat_message(item["role"]).write(item["content"])


# ======================================================
# ALWAYS SHOW INPUT MODE SELECTOR
# ======================================================
mode = st.radio(
    "Choose Input Mode:",
    ["Text Input", "Voice Input"],
    horizontal=True
)

user_input = None   # Will hold the text message from text or voice


# ======================================================
# ALWAYS SHOW INPUT CONTROLS
# ======================================================
st.divider()
st.subheader("Your Input")

# -------------------------------
# Voice Input Mode
# -------------------------------
if mode == "Voice Input":

    audio = st.audio_input("Record your message...", sample_rate=48000)

    if audio is not None:
        st.success("Audio recorded! Click below to convert to text.")

        if st.button("Convert Voice → Text"):
            try:
                audio_bytes = audio.getvalue()
                files = {"file": ("message.wav", audio_bytes, "audio/wav")}

                response = requests.post("http://localhost:8000/api/stt/file", files=files)

                if response.status_code == 200:
                    data = response.json()
                    user_input = data["text"]
                    st.info(f"Transcribed Text: **{user_input}**")
                else:
                    st.error(f"API Error {response.status_code}: {response.text}")

            except Exception as e:
                st.error(f"Error contacting API: {e}")

# -------------------------------
# Text Input Mode
# -------------------------------
else:
    user_input = st.chat_input("Ask ATOM anything...")


# ======================================================
# CHAT PROCESSING
# ======================================================
if user_input:
    # Save user message
    st.session_state.history.append({"role": "user", "content": user_input})
    st.chat_message("user").write(user_input)

    # Stream assistant reply
    full_reply = ""
    assistant_box = st.chat_message("assistant")

    with assistant_box:
        placeholder = st.empty()
        try:
            for chunk in stream_chat(user_input):  # yields chunks of text
                full_reply += chunk
                placeholder.write(full_reply)
        except Exception as e:
            st.error(f"Error during streaming: {e}")
            full_reply = "An error occurred while generating the response."

    # Save assistant message
    st.session_state.history.append({"role": "assistant", "content": full_reply})

    # Save history to file
    save_history(st.session_state.history)

    # Refresh UI cleanly
    st.rerun()

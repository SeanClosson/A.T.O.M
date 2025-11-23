# **README – ATOM**

### *A Modular Local AI Assistant for Voice Interaction, Automation & Computer Vision*

---
## 📘 Overview

**ATOM (Autonomous Tool-Orchestrating Operation Machine)** is a modular, local AI assistant designed to provide natural language interaction, execute structured tasks through tool-based function calling, perform basic image analysis, and interface with physical robotic devices.

The system emphasizes:

* modularity,
* privacy,
* robustness,
* and real-world functionality.

ATOM currently uses **RealtimeSTT** (terminal-only speech input) and runs on **Qwen/Qwen3-VL-4B locally through LM Studio** as the primary language model backend.

This project is under active development and is intended to demonstrate applied engineering, AI integration, and robotics control capabilities for academic evaluation.
---

<br>

# ⚙️ Current Capabilities

### 🎤 Speech Processing

* Real-time streaming speech recognition (RealtimeSTT)
* Terminal-only STT interface *(not integrated into Streamlit UI yet)*
* Command and task invocation

### 🧠 Local Language Model

* Qwen Qwen3-VL-4B via LM Studio
* Tool-calling enabled
* Vision-capable model support

> **Important:** If replacing the model, select a vision-capable model to maintain image analysis functionality.

### 🖼 Image Processing

* Live camera capture
* Local image analysis pipeline
* Integrated tool: `capture_and_analyze_photo`

### 🤖 Physical Presence

ATOM provides limited physical embodiment through:

* robotic greetings
* gesture actions
* quadruped dance motion

### 🛠 Tool System

Provided tools:

```
get_temperature
get_date_time
get_humidity
toggle_wled
get_light_state
create_file
web_search
create_pdf
search_wikipedia
set_timer
list_timers
cancel_timer
get_weather
geocode_city
convert_currency
ip_geolocation
fetch_and_parse
calculate
capture_and_analyze_photo
greet_user
dance_quadruped
```

### 🗂 System Status

* No TTS at present
* No wake word yet
* No long-term memory
* No calendar sync
* No persistent storage layer

---

<br>

# 🔭 Planned Development

* wake word activation
* expanded robotics integrations
* Streamlit STT support
* enhanced embodiment behavior

---

<br>

# 💻 Platform Notes

This project has currently **only been tested under:**

* **Arch Linux**
* using **Conda** as the virtual environment manager

Other OS / environment configurations have not been evaluated yet.

---

<br>

# 🛡️ Project Principles

* local-first execution
* reliability over quantity of features
* incremental iteration
* modular architecture
* focus on practical real-world usage

---

<br>

# 🏗 System Architecture (Current)

```
┌─────────────────────────┐
│  Microphone (Terminal)  │
└───────────┬─────────────┘
            │
            ▼
┌─────────────────────────┐
│      RealtimeSTT        │
└───────────┬─────────────┘
            │
            ▼
┌─────────────────────────┐
│ LM Studio Backend (LLM) │
│ Qwen3-VL-4B             │
└───────────┬─────────────┘
            │
            ▼
  Tool Execution Layer
            ▼
      System + APIs + Robotics
```

---

<br>

# 🧰 Tech Stack

| Component          | Technology         |
| ------------------ | ------------------ |
| Speech Recognition | RealtimeSTT        |
| LLM Backend        | LM Studio          |
| LLM Model          | `qwen/qwen3-vl-4b` |
| UI                 | Streamlit          |
| API Layer          | FastAPI            |
| Robotics Interface | Python modules     |
| PDF Engine         | reportlab          |
| Web Parser         | BeautifulSoup      |

---

<br>

# 📦 Installation

### 1. Clone Repository

```bash
git clone https://github.com/AtifUsmani/ATOM.git
cd ATOM
```

### 2. Create Conda Environment

*(ATOM has only been tested using Conda on Arch Linux)*

```bash
conda create -n atom python=3.13.9
conda activate atom
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure Application

#### 4.1 Configure runtime parameters:

Inside the project root, edit:

```
example.yaml
```

Update the values.
Then rename it to:

```
config.yaml
```

This file is read at startup.

#### 4.2 Configure the system prompt

Rename the template file:

```
template.txt → prompt.txt
```

Then edit `prompt.txt` to modify the system behavior / personality.

---

### 5. Start ATOM

To start ATOM in **command-line mode (with STT):**

```bash
python main.py      # this starts ATOM in CLI
```

#### OR

To start the **API & Web UI mode:**

```bash
uvicorn api.server:app --reload
streamlit run frontend/main.py
```

---

## 🔧 LM Studio Setup

* install `qwen/qwen3-vl-4b`
* load the model
* start local inference server
* enable function-calling
* set the context length to at least 8,000 tokens for optimal stability

> **Note:** lower token limits may degrade response reliability and tool execution consistency.

---

<br>

# 🎯 Usage Examples

* “Search Wikipedia for Alan Turing.”
* “Toggle WLED.”
* “Analyze this photo.”
* “Make the robot greet me.”

<br>
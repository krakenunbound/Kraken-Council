
# 🦑 Kraken Kouncil v4.2.1 + GPU

Orchestrate a **council of local AI models** with multi-round debates, beautiful model icons, optional web search, and a real‑time GPU monitor — all in a Qt / PySide6 desktop app.

---

## ✨ Highlights of This Release

### 🎯 v4.2.1 – Bug Fix & Polish Pass

- 🛠️ **Voting is rock solid** – critiques can use contractions like `model's`, `it's`, `don't` without breaking JSON.
- 📅 **Better sense of time** – when web search is enabled, models clearly see the current date in their context.
- 🔗 **Source citations** – web‑powered answers include `[1]`, `[2]`‑style references so you can see where info came from.
- 😈 **Ruthless critiques** – the critique phase is tougher and more specific, leading to genuinely better refinements.
- 🐧 **Cross‑platform icons** – `.png` / `.PNG` work properly on Linux and friends.
- 🎨 **Sharper avatars** – icons are scaled for better visibility without looking oversized.
- 🚦 **Strict Concurrency** – `max_concurrency` is now strictly enforced during debates to prevent system overload.
- 🧠 **Smarter Debates** – Web search context is now preserved during the debate phase, preventing hallucinations.

See **CHANGELOG.md** for detailed notes and technical references.

---

### 🎮 GPU Monitor – Optional but Awesome

If you have an NVIDIA GPU, Kraken Kouncil can show a compact **GPU Monitor** in the left sidebar:

- 🌡️ Temperature, with color‑coded safety bands
- ⚡ Utilization percentage
- 💾 VRAM usage (used / total)
- 🏷️ GPU name / model
- 🔄 Updates roughly every 2 seconds
- 🛡️ Graceful fallback: if no GPU or no library → “No GPU detected” instead of a crash

For a 2‑step setup and quick color legend, check **GPU_SETUP_QUICK.md**.  
For deeper detail and examples, see **GPU_MONITORING_ADDED.md**.

---

## 🚀 Getting Started

### 1️⃣ Requirements (Typical Setup)

- **Python 3.12+** installed  
- **PySide6** and a few supporting libraries:
  ```bash
  pip install PySide6 aiohttp requests
  ```
- Optional but recommended:
  ```bash
  pip install pyqtdarktheme
  ```

> 💡 Tip: Use a virtualenv if you like keeping things tidy:
> ```bash
> python -m venv .venv
> source .venv/bin/activate  # Linux / macOS
> .venv\Scripts\activate   # Windows
> ```

### 2️⃣ Running the App

From this folder:

```bash
python3 kraken_council_v4_2_1.py
```

On Windows you can usually just double‑click the file, but running from a terminal is recommended so you can see logs.

### 3️⃣ Optional: Enable GPU Monitoring

If you have a supported **NVIDIA GPU** and want the GPU Monitor panel:

```bash
pip install nvidia-ml-py
# or
pip install nvidia-ml-py3
```

Then run:

```bash
python3 kraken_council_v4_2_1.py
```

In the **left sidebar** you should see, from top to bottom:

1. ✅ Model list (checkboxes)  
2. 📊 Stats panel  
3. 🎮 **GPU Monitor** (new)  
4. 🏆 Leaderboard  

If no compatible GPU is found, the GPU panel will simply say **“No GPU detected”** and the rest of the app still works perfectly.

---

## 🧠 Feature Overview

### 🗣️ Agentic Debate System

- Run multi‑round debates across multiple models.
- Each round has a **critique** and **refinement** phase.
- A status line keeps you informed:  
  `🗣️ Debate Round 1/2 → 💭 Critiquing (2/3) → 🔧 Refining (3/3)`
- Final answers are voted on using a rich set of criteria (relevance, clarity, completeness, accuracy, helpfulness).

### 🏛️ Hybrid Arena Layout

Kraken Kouncil uses a **hybrid layout** so the UI stays readable even with lots of models:

- Left sidebar: a compact checklist of all available models.
- Center arena: big, detailed cards only for the models you’ve checked.
- Each arena card includes:
  - Model name + backend badge (e.g. 🎬 LM Studio / 🦙 Ollama)
  - Persona dropdown (nine one‑click personas)
  - Status / progress indicators
  - Streaming response output

### 🌐 Web Search (Optional)

Kraken Kouncil can call **Google Programmable Search Engine (PSE)** before the models respond:

- Configure an API key + Search Engine ID in the **Settings → Web Search** section.
- When enabled, the app shows a **“🔍 Searching web…”** status and injects formatted results (title, URL, snippet) into the prompt.
- Ideal for:
  - News & current events
  - Prices, schedules, fresh data
  - Anything where “today / this week / recently” matters

If web search is not configured or fails, the app falls back gracefully to pure local‑model behavior.

### 🎨 Model Icons & Visual Identity

The app includes a smart icon system for model families:

1. **PNG icons** from your local `icons/` folder (best).
2. **Emoji fallbacks** for known families (Llama, Gemma, Qwen, Mistral, Phi, Falcon, Yi, DeepSeek, etc.).
3. **Initials** when all else fails.

Icons are clipped to a circle, rendered with nice borders, and scaled for good readability in the avatars.

---

## 🧪 Quick Sanity Checklist

When you first spin up the app, here’s a quick checklist to make sure everything feels right:

- [ ] App starts with no exceptions in the terminal.
- [ ] **Help → About** shows version **4.2.1** and lists the bug‑fix highlights.
- [ ] Debates run end‑to‑end without JSON / voting errors (even if your critiques use contractions).
- [ ] If web search is configured:
  - [ ] Asking “What’s today’s date?” or a similar query yields the correct date.
  - [ ] Web‑based answers cite sources like `[1]`, `[2]`.
- [ ] Icons appear properly on your platform (including `.PNG` files on Linux).  
- [ ] If GPU monitoring is installed:
  - [ ] “🎮 GPU Monitor” panel appears in the left sidebar.
  - [ ] GPU stats update while models generate.

If all of that looks good, you’re in great shape. 💚

---

## 📁 What’s in This Folder?

- `kraken_council_v4_2_1.py` – Main application (all current features + fixes + GPU support).
- `README.md` – This file, your high‑level overview and quick start.
- `CHANGELOG.md` – Full version history and technical changes.
- `GPU_SETUP_QUICK.md` – Two‑step GPU setup and color legend.
- `GPU_MONITORING_ADDED.md` – A deep dive into the GPU panel behavior.
- `DOWNLOAD_HERE.md` – A short, friendly “start here” card you can share or embed.

(Everything else from earlier dev sessions — summaries, logs, meta‑notes — is optional. You can keep them separately in a `/docs` folder or toss them if you like.)

---

## 🔗 Handy External Links

These aren’t required, but they’re nice companions to Kraken Kouncil:

- 🐍 **Python** – official downloads & docs: https://www.python.org/
- 🪟 **PySide6 (Qt for Python)** – GUI docs: https://doc.qt.io/qtforpython-6/
- 💻 **LM Studio** – run local models with a polished UI: https://lmstudio.ai/
- 🐋 **Ollama** – run local LLMs with a simple workflow: https://ollama.com/

---

Happy counciling — may your models debate passionately but converge gracefully. 🦑⚔️

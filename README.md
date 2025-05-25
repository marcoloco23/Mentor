<p align="center">
  <img src="docs/logo.png" alt="Ted Logo" width="120"/>
</p>

<div align="center">

# Ted: Your Lifelong AI Companion

<h3>
<a href="#-architecture">Architecture</a> | <a href="#-quickstart">Quickstart</a> | <a href="#-features">Features</a> | <a href="#-roadmap">Roadmap</a> | <a href="#-contributing">Contributing</a> | <a href="#-license">License</a>
</h3>

</div>

---

Ted is a conversational AI that **remembers what matters** and supports you with playful, honest, and sometimes cheeky advice. Think of Ted as your loyal best friend—always there to make you laugh, help you grow, and get you through anything.

---

## ✨ Features

- **Lifelong friendship:** Builds an evolving knowledge base about *you*: your stories, quirks, and dreams.
- **Playful honesty:** Gives you the real talk, but with warmth and wit—never boring, always on your side.
- **Actionable support:** Each answer is concise, specific, and tailored to you—not generic self-help.
- **Privacy & control:** All memories live in a dedicated memory layer (Mem0). You can inspect, export, or delete them at any time.
- **Pluggable LLM:** Uses OpenAI GPT-4.1 by default, but is easily extensible.
- **Modern UI:** Streamlit-based, with token streaming for a responsive chat experience.

---

## 🚀 Mobile App & API Quickstart

### Prerequisites
- Node.js (v18+ recommended)
- Python 3.11+
- [Expo CLI](https://docs.expo.dev/get-started/installation/) (install with `npm install -g expo-cli`)
- (For iOS simulator) Xcode, or Expo Go app for physical device

### 1. Backend API (FastAPI)

```sh
# Local development
uvicorn main:app --host 0.0.0.0 --port 8000 --reload

# For mobile development with Expo Go, also run in a separate terminal:
ngrok http 8000
```
- The API will be available at `http://localhost:8000` for web development
- When using ngrok, note the https URL (e.g., `https://xxxx-xx-xx-xxx-xxx.ngrok-free.app`) and update it in `mobile/src/utils/apiBaseUrl.ts`

### 2. Mobile App (Expo/React Native)

```sh
cd mobile
npm install
npx expo start         # For local development using LAN
# OR
npx expo start --tunnel # For more reliable connection across networks
```
- Press `i` to launch the iOS simulator, or scan the QR code with Expo Go on your device.
- When using Expo Go on a physical device, make sure to:
  1. Keep the API server running
  2. Keep ngrok tunnel running
  3. Update the ngrok URL in `apiBaseUrl.ts`

---

## 🚀 Quickstart

```bash
pip install -r requirements.txt
streamlit run app.py
```

Set the following environment variables (see `.env.example`):

```env
OPENAI_API_KEY=sk-…
MEM0_API_KEY=mem-…
```

---

## 🏗️ Architecture

| Layer      | Tech                              | Purpose                                             |
|------------|-----------------------------------|-----------------------------------------------------|
| **UI**     | Streamlit                         | Lightweight chat front‑end with token streaming      |
| **Agent**  | `Ted` class                       | Orchestrates retrieval → LLM → async store          |
| **Memory** | Mem0                              | Vector + metadata store for long‑term memories       |
| **LLM**    | OpenAI GPT‑4.1 (pluggable)        | Generates and streams responses                     |

> **Flow per turn:**
> 1. Retrieve top memories `k=5` (recency‑weighted, deduped)
> 2. Inject them into the system prompt and stream the answer
> 3. Persist the dialogue asynchronously in the background

---

## 📚 Key Files

| Path              | Description                          |
|-------------------|--------------------------------------|
| `src/ted.py`      | Core agent logic and streaming helper |
| `src/memory.py`   | Retrieval, re‑ranking, async persistence |
| `src/llm.py`      | Thin wrapper around the OpenAI client |
| `app.py`          | Streamlit UI                         |

---

## 📝 Example Usage

```python
import os
from ted import Ted

ted = Ted(openai_api_key=os.getenv("OPENAI_API_KEY"), mem0_api_key=os.getenv("MEM0_API_KEY"))
response = ted.ask("How can I improve my productivity?")
print(response)
```

---

## 🗺️ Roadmap

- **Multi-user auth** with secure per-user key management
- **Scheduled reflections:** daily/weekly check-ins driven by stored goals
- **Voice mode** using WebRTC + Whisper real-time transcription
- **Plugin hooks** for calendar, tasks, or custom knowledge bases

---

## 🤝 Contributing

1. Fork & clone the repo
2. `pre-commit install` for linting hooks
3. Submit a PR with a concise description; small, focused patches are easier to review!

**Contribution Guidelines:**
- Focus on clarity, maintainability, and minimalism.
- All new features should include tests and documentation.
- Bug fixes are welcome—please include a regression test.
- For larger changes, open an issue first to discuss your proposal.

---

## 🧪 Running Tests

```sh
python -m unittest discover tests
```

---

## 📝 License

MIT — see [`LICENSE`](LICENSE).

---

<p align="center"><em>Crafted with loyalty, wit, and a dash of mischief—just like Ted.</em></p>

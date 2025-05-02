<p align="center">
  <img src="docs/logo.png" alt="Mentor Logo" width="120"/>
</p>

<div align="center">

# Mentor: Your Personal AI Coach

<h3>
<a href="#-architecture">Architecture</a> | <a href="#-quickstart">Quickstart</a> | <a href="#-features">Features</a> | <a href="#-roadmap">Roadmap</a> | <a href="#-contributing">Contributing</a> | <a href="#-license">License</a>
</h3>

</div>

---

Mentor is a conversational AI that **remembers what matters** and guides you with direct, no‑fluff advice. Think of it as a seasoned mentor who interviews you, learns your goals, and asks sharp follow‑up questions to accelerate your growth.

---

## ✨ Features

- **Long-term relationship:** Builds an evolving knowledge base about *you*: your goals, preferences, and past decisions.
- **Socratic guidance:** Asks questions that surface blind spots and spark self-reflection.
- **Actionable insight:** Each answer is concise, specific, and backed by context—not generic self-help jargon.
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
uvicorn main:app --reload
```
- The API will be available at `http://localhost:8000`.

### 2. Mobile App (Expo/React Native)

```sh
cd mentor-mobile
npm install
npx expo start
```
- Press `i` to launch the iOS simulator, or scan the QR code with Expo Go on your device.
- The app will connect to the backend at `http://localhost:8000` by default (see `src/api/mentorApi.ts`).

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
| **Agent**  | `Mentor` class                    | Orchestrates retrieval → LLM → async store          |
| **Memory** | Mem0                              | Vector + metadata store for long‑term memories       |
| **LLM**    | OpenAI GPT‑4.1 (pluggable)    | Generates and streams responses                     |

> **Flow per turn:**
> 1. Retrieve top memories `k=5` (recency‑weighted, deduped)
> 2. Inject them into the system prompt and stream the answer
> 3. Persist the dialogue asynchronously in the background

---

## 📚 Key Files

| Path              | Description                          |
|-------------------|--------------------------------------|
| `src/mentor.py`   | Core agent logic and streaming helper |
| `src/memory.py`   | Retrieval, re‑ranking, async persistence |
| `src/llm.py`      | Thin wrapper around the OpenAI client |
| `app.py`          | Streamlit UI                         |

---

## 📝 Example Usage

```python
import os
from mentor import Mentor

mentor = Mentor(openai_api_key=os.getenv("OPENAI_API_KEY"), mem0_api_key=os.getenv("MEM0_API_KEY"))
response = mentor.ask("How can I improve my productivity?")
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

<p align="center"><em>Crafted with curiosity and a dash of Socratic questioning.</em></p>

# 🎙️ Meeting Intelligence System

[![Live Demo](https://img.shields.io/badge/🚀_Live_Demo-Click_Here-FF4B4B?style=for-the-badge)](https://meeting-intelligence-system-fcvch9kn7jmw6bqffy2hwj.streamlit.app/)
[![Python](https://img.shields.io/badge/Python-3.8+-3776AB?style=flat-square&logo=python)](https://python.org)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.32-FF4B4B?style=flat-square&logo=streamlit)](https://streamlit.io)
[![License](https://img.shields.io/badge/License-MIT-green?style=flat-square)](LICENSE)

> Upload a meeting recording → Get transcript, summary, and action items in under 60 seconds.

---

## 📸 Demo

| Upload & Auto-route | Transcription + Summary |
|---|---|
| ![Upload](c:\Users\Shaina Hussain\OneDrive\Pictures\Screenshots\Screenshot 2026-03-06 102427.png) | ![Summary](c:\Users\Shaina Hussain\OneDrive\Pictures\Screenshots\Screenshot 2026-03-06 102639.png) |

| Meeting Summary | Action Items |
|---|---|
| ![Summary Output](c:\Users\Shaina Hussain\OneDrive\Pictures\Screenshots\Screenshot 2026-03-06 102800.png) | ![Action Items](c:\Users\Shaina Hussain\OneDrive\Pictures\Screenshots\Screenshot 2026-03-06 102844.png) |

---

## 🚀 Quick Start

```bash
git clone https://github.com/ShainaHussain/Meeting-Intelligence-System.git
cd Meeting-Intelligence-System
pip install -r requirements.txt

# Add your API key
echo "GROQ_API_KEY=your_key_here" > .env

streamlit run app.py
```

Get a **free** Groq API key at [console.groq.com](https://console.groq.com)

---

## ✅ What It Does

Upload any meeting recording and get back:

- **📊 AI Summary** — 3-5 sentence overview of the entire meeting
- **✅ Action Items** — structured list with owner, task, and deadline
- **📝 Full Transcript** — complete text of everything said
- **💾 Meeting History** — all past meetings saved locally
- **📥 Download Report** — full report as a `.txt` file

---

## ⚡ How Fast

| Meeting Length | Processing Time |
|---|---|
| 10 minutes | ~30 seconds |
| 30 minutes | ~1 minute |
| 1 hour | ~2-3 minutes |

---

## 🧠 How It Works

```
Upload Audio
     ↓
Smart Routing (file size check)
     ├── < 25MB  → Groq Whisper API  (fast, free)
     └── > 25MB  → AssemblyAI        (up to 5GB)
     ↓
Validation (word count + keyword check)
     ↓
LLM Intelligence — Llama 3.3 70B via Groq
     ├── Meeting Summary
     └── Action Item Extraction (chunked for long meetings)
     ↓
SQLite DB → Save meeting record
     ↓
Display + Download
```

**Key design decisions:**
- **Hybrid transcription** — auto-routes between Groq and AssemblyAI based on file size. No manual selection needed.
- **Chunking strategy** — splits transcripts into 5000-word chunks to handle token limits. Works for 3+ hour meetings.
- **Lazy client init** — Groq client created only when a key exists, preventing startup crashes on cloud deployment.
- **3-layer secret management** — checks `st.secrets` → `.env` → sidebar input. Same code works locally and in production.

---

## 🛠️ Tech Stack

| Layer | Technology | Why |
|---|---|---|
| UI | Streamlit | Rapid deployment, no frontend code needed |
| Transcription (small) | Groq Whisper API | Free, fast, state-of-the-art |
| Transcription (large) | AssemblyAI | Handles async, up to 5GB |
| LLM | Llama 3.3 70B via Groq | Free tier, fast inference |
| Database | SQLite | Zero setup, built into Python |
| Deployment | Streamlit Cloud | Native support, free tier |

---

## 💰 Cost

**Completely free** for most use cases.

- Groq API — free tier handles ~100 meetings/day
- AssemblyAI — 5 hours/month free (for large files only)
- Hosting — Streamlit Cloud free tier

---

## 📁 Project Structure

```
Meeting-Intelligence-System/
├── app.py              # Main application (transcription + LLM + UI)
├── requirements.txt    # Dependencies
├── learning_log.md     # Day-by-day build journal
├── .gitignore
└── README.md
```

---

## 🗺️ Roadmap

**Completed ✅**
- Hybrid transcription (Groq + AssemblyAI auto-routing)
- AI meeting summary
- Action item extraction with chunking
- 95+ language support with auto-translation
- SQLite meeting history
- Download complete report

**In Progress 🔄**
- Speaker diarization (who said what)
- PDF report export

**Planned 📋**
- Persistent cloud database (Supabase)
- Email report to yourself
- Search across past meetings
- FastAPI wrapper for programmatic access

---

## ⚠️ Known Limitations

- SQLite resets on server restart (Streamlit Cloud) — use locally for persistent history
- Speaker diarization requires AssemblyAI key (not available via Groq)
- No real-time transcription — file upload only

---

## 📖 Learning Log

This project was built incrementally over several days. See [`learning_log.md`](learning_log.md) for a day-by-day breakdown of what was built, problems hit, and how they were solved. A real record of the engineering process.

---

## License

MIT — free to use and modify.

---

**Built by [Shaina Hussain](https://github.com/ShainaHussain)**  
[LinkedIn](https://www.linkedin.com/in/shaina-hussain) · [LeetCode](https://leetcode.com/u/Shaina01/) · [Email](mailto:iamshainah@gmail.com)
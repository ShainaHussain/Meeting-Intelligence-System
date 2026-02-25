# 🎙️ Meeting Intelligence System

AI-powered tool that transcribes meetings, generates summaries, and extracts action items. Supports 95+ languages.

**[Quick Start](#quick-start) • [Features](#features) • [GitHub](https://github.com/ShainaHussain/Meeting-Intelligence-System)**

---

## Why This?

Upload meeting audio → Get instant summary + action items. No more note-taking.

**Example Output:**
```
📊 Summary: Team discussed Q1 goals. Marketing launches campaign March 15.
Engineering fixes bugs before release. Next meeting Friday.

✅ Action Items:
- Sarah: Launch campaign (Due: March 15)
- Dev Team: Fix critical bugs (Due: Before release)
```

---

## Quick Start

```bash
git clone https://github.com/ShainaHussain/Meeting-Intelligence-System.git
cd Meeting-Intelligence-System
pip install -r requirements.txt
echo "GROQ_API_KEY=your_key_here" > .env
streamlit run app.py
```

Get a free Groq API key at [console.groq.com](https://console.groq.com)

---

## Features

- ✅ Transcribes audio (MP3, WAV, M4A)
- ✅ Translates 95+ languages to English
- ✅ Generates 3-5 sentence AI summary
- ✅ Extracts action items with owners & deadlines
- ✅ Meeting history saved to local database
- ✅ Handles files up to 25 MB (Groq) or 5 GB (AssemblyAI)

**Speed:** 10-min meeting → ~30 seconds | 1-hour meeting → ~2-3 minutes  
**Cost:** Completely FREE with Groq API free tier

---

## Tech Stack

- **Frontend:** Streamlit
- **AI:** Groq Whisper, Llama-3.3-70B, AssemblyAI
- **Database:** SQLite (local meeting history)
- **Language:** Python 3.8+

---

## License

MIT

---

**Built by [Shaina Hussain](https://github.com/ShainaHussain) · ⭐ Star if useful!**
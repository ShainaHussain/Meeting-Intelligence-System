# 🎙️ Meeting Intelligence System

AI-powered tool that transcribes meetings, generates summaries, and extracts action items. Supports 95+ languages.

**[Demo](#) • [Quick Start](#quick-start) • [Features](#features)**

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
# 1. Install
git clone https://github.com/ShainaHussain/Meeting-Intelligence-System.git
cd Meeting-Intelligence-System
pip install -r requirements.txt

# 2. Get free API key from console.groq.com

# 3. Create .env file
echo "GROQ_API_KEY=your_key_here" > .env

# 4. Run
streamlit run app.py
```

That's it. Opens in browser.

---

## Features

**What it does:**
- ✅ Transcribes audio (MP3, WAV, M4A)
- ✅ Translates 95+ languages to English
- ✅ Generates 3-5 sentence summary
- ✅ Extracts action items with owners & deadlines
- ✅ Handles files up to 5GB

**How fast:**
- 10 min meeting → ~30 seconds
- 1 hour meeting → ~2-3 minutes

**Cost:**
- Completely FREE for most use cases
- Uses Groq API (free tier is generous)

---

## How It Works

```
Upload audio → Auto-transcribe → AI analyzes → Get results
     ↓              ↓                ↓              ↓
  Your file    Groq/AssemblyAI   Llama-3.3    Summary + Items
```

**Smart routing:**
- Small files (<25MB) → Groq (fastest, free)
- Large files → AssemblyAI (5hr/month free)
- You don't choose, system auto-picks best option

---

## Tech Stack

- **Frontend:** Streamlit
- **AI:** Groq Whisper, Llama-3.3-70B, AssemblyAI
- **Language:** Python 3.8+

---

## Roadmap

**Done ✅**
- Transcription with auto-translation
- AI summary generation
- Action item extraction
- Hybrid processing (smart file routing)

**Next 🔜**
- Key topics extraction
- PDF reports
- Speaker identification
- Search in transcripts

---

## FAQ

**Q: Does it cost money?**  
A: FREE with Groq API key. Optional AssemblyAI for large files (5hr/month free).

**Q: What languages?**  
A: 95+ including English, Hindi, Spanish, French, etc. Auto-translates to English.

**Q: File size limits?**  
A: Up to 25MB free (Groq), up to 5GB with AssemblyAI.

**Q: How accurate?**  
A: Very. Uses state-of-the-art Whisper model (same as OpenAI).

---

## Contributing

PRs welcome! This is a learning project built in 4 days.

---

## License

MIT - Free to use and modify

---

**Built by [Shaina Hussain](https://github.com/ShainaHussain) • ⭐ Star if useful!**
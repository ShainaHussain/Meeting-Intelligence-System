# Learning Log

## Day 1 - Audio Upload + Transcription

### Date: [1 Feb 2026]

### Built:
- Streamlit app: upload audio → transcribe to text
- Files save to `uploads/` folder
- Whisper AI generates transcripts

### Key Problem Solved:
**FFmpeg Error on Windows/Anaconda**
- Error: `[WinError 2] The system cannot find the file specified`
- Cause: Whisper needs FFmpeg, but Anaconda's FFmpeg not in system PATH
- Fix: Detect Anaconda FFmpeg path, add to PATH programmatically

### Core Concepts:
1. **Streamlit**: `st.file_uploader()`, caching with `@st.cache_resource`
2. **File handling**: Binary mode (`wb`) for audio, text mode (`w`) for transcripts
3. **Whisper**: Local model, free, caches after first download (~140MB)
4. **PATH**: Environment variable for executable locations

### Code Patterns:
```python
# Create folder if missing
UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)

# Fix FFmpeg for Anaconda
conda_base = Path(sys.executable).parent
ffmpeg_path = conda_base / "Library" / "bin" / "ffmpeg.exe"
os.environ["PATH"] = str(ffmpeg_path.parent) + os.pathsep + os.environ["PATH"]

# Cache heavy model
@st.cache_resource
def load_model():
    return whisper.load_model("base")
```

### Next: Extract action items from transcripts
### Status: ✅ Working

## Day 2 - Action Item Extraction + Production Features

### Date: [2 Feb 2026]

### Built:
- Action item extraction from transcripts using Groq LLM
- Multilingual support (auto-translate 95+ languages to English)
- Content validation (detects non-meeting audio)
- Chunking strategy for long transcripts (handles 3+ hour meetings)
- File size handling up to 200MB

### Key Problem Solved:
**Long File Processing & Token Limits**
- Challenge: 2-hour meetings exceed LLM token limits (~32K tokens)
- Solution: Split transcripts into 5000-word chunks, process separately, deduplicate results
- Also identified: Local Whisper too slow (1 hour audio = 20-30 min) - noted Groq Whisper API as future optimization

### Core Concepts:
1. **Prompt Engineering**: Structured prompts to extract action items in specific format
2. **LLM Integration**: Groq API with Llama-3.3-70b for free, fast inference
3. **Session State**: `st.session_state` to persist data between button clicks
4. **Chunking**: Handle content exceeding token/context limits
5. **Multilingual AI**: Whisper's `task="translate"` for automatic translation

### Code Patterns:
```python
# LLM for structured extraction
response = groq_client.chat.completions.create(
    model="llama-3.3-70b-versatile",
    messages=[{"role": "user", "content": prompt}],
    temperature=0.3
)

# Auto-translate any language to English
result = model.transcribe(file_path, task="translate")

# Chunking for long transcripts
def chunk_transcript(text, max_words=5000):
    words = text.split()
    return [' '.join(words[i:i+max_words]) for i in range(0, len(words), max_words)]

# Session state for multi-step workflow
st.session_state.transcript = transcript_text
```

### Next: Deploy system OR optimize speed with Groq Whisper API
### Status: ✅ Working

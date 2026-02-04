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

## Day 3 - Hybrid Architecture & Speed Optimization

### Date: [3 Feb 2026]

### Built:
- Hybrid transcription system with auto-routing (Groq + AssemblyAI)
- Smart file size detection: small files → Groq, large files → AssemblyAI
- Removed local Whisper dependency (too slow for production)
- File handling up to 5GB with automatic service selection

### Key Problem Solved:
**Speed Bottleneck with Local Whisper**
- Problem: Local Whisper too slow (1 hour audio = 20-30 min processing)
- Cause: CPU processing vs cloud GPU processing
- Solution: Switched to API-based transcription with intelligent routing
- Result: 10-50x faster (1 hour audio = 2-3 min)

### Core Concepts:
1. **Hybrid Architecture**: Auto-route between services based on file size
2. **API Integration**: Groq Whisper (free, 25MB limit) + AssemblyAI (5hr/month free, 5GB limit)
3. **Smart Routing**: System picks optimal service automatically
4. **Cost Optimization**: Use free Groq when possible, AssemblyAI only for large files
5. **Fallback Logic**: Graceful error handling when services unavailable

### Code Patterns:
```python
# Smart auto-routing
def smart_transcribe(file_path, file_size_mb):
    if file_size_mb < 20:
        return transcribe_with_groq(file_path)  # Fast & free
    elif ASSEMBLYAI_AVAILABLE:
        return transcribe_with_assemblyai(file_path)  # Large files
    else:
        raise Exception("Need AssemblyAI for large files")

# Groq Whisper API (replaced local Whisper)
transcription = groq_client.audio.transcriptions.create(
    file=audio_file,
    model="whisper-large-v3-turbo"
)

# AssemblyAI for large files
transcriber = aai.Transcriber()
transcript = transcriber.transcribe(str(file_path))
```

### Next: Deploy system (Railway/Streamlit Cloud) + Add FastAPI wrapper
### Status: ✅ Production-ready
## Day 4 - AI Meeting Summary & Intelligence Layer

### Date: [4 Feb 2026]

### Built:
- AI-powered meeting summary generation (3-5 sentence overview)
- Auto-summary immediately after transcription
- Smart handling of long transcripts (uses first 3000 words for summary)
- Complete report download (Summary + Action Items + Transcript)
- Improved UI with collapsible transcript section

### Key Problem Solved:
**User Overwhelm with Long Transcripts**
- Problem: Users got 3000+ word transcripts and didn't want to read everything
- User need: "Just tell me what happened in the meeting"
- Solution: Auto-generate concise 3-5 sentence summary using LLM
- Result: Users get main points in 5 seconds without reading full transcript

### Core Concepts:
1. **Multi-LLM Orchestration**: Using same Groq client for both summarization and extraction
2. **Prompt Engineering for Summaries**: Different prompts for different tasks (summary vs action items)
3. **Smart Input Truncation**: Limit to 3000 words to avoid token limits while preserving context
4. **User-Centric Design**: Show summary first, hide full transcript in expander
5. **Temperature Tuning**: 0.5 for summaries (natural language) vs 0.3 for extraction (precision)

### Code Patterns:
```python
# Generate summary with LLM
def generate_summary(transcript_text):
    # Truncate if too long
    if len(transcript_text.split()) > 3000:
        summary_input = ' '.join(transcript_text.split()[:3000])
    else:
        summary_input = transcript_text
    
    prompt = """Create a brief summary (3-5 sentences) that captures:
    1. Main purpose/topic
    2. Key decisions
    3. Important discussion points
    4. Next steps"""
    
    response = groq_client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        temperature=0.5,  # Natural language generation
        max_tokens=300    # Limit summary length
    )

# Auto-generate after transcription
with st.spinner("✨ Generating AI summary..."):
    summary = generate_summary(transcript_text)
    st.session_state.summary = summary

# UI organization: Summary → Action Items → Transcript
st.subheader("📊 Meeting Summary")
st.info(summary)  # Prominent display

with st.expander("📝 Full Transcript"):  # Collapsed by default
    st.text_area(transcript_text)
```

### What Users Get Now:
**Complete 3-Layer Analysis:**
1. 📊 **Summary**: Quick overview (3-5 sentences)
2. ✅ **Action Items**: Structured task list with owners and deadlines
3. 📝 **Transcript**: Full text for reference

### Next: Key Topics Extraction + PDF Report Generation
### Status: ✅ Working
### Time Spent: ~3 hours
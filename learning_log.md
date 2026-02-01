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
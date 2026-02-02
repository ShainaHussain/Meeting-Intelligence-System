import streamlit as st
from pathlib import Path
import whisper
import os
import sys
from groq import Groq
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Setup
UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)

# Find FFmpeg in Anaconda
if sys.platform == "win32":
    conda_base = Path(sys.executable).parent
    ffmpeg_path = conda_base / "Library" / "bin" / "ffmpeg.exe"
    if ffmpeg_path.exists():
        os.environ["PATH"] = str(ffmpeg_path.parent) + os.pathsep + os.environ["PATH"]

# Initialize Groq client
groq_client = Groq(api_key=os.getenv("GROQ_API_KEY"))

# Load Whisper model (only once)
@st.cache_resource
def load_model():
    return whisper.load_model("base")

def chunk_transcript(text, max_words=5000):
    """Split long transcript into chunks for LLM processing"""
    words = text.split()
    chunks = []
    
    for i in range(0, len(words), max_words):
        chunk = ' '.join(words[i:i + max_words])
        chunks.append(chunk)
    
    return chunks

def validate_transcript(transcript):
    """Check if transcript looks like a meeting"""
    
    word_count = len(transcript.split())
    if word_count < 50:
        return False, f"Transcript too short ({word_count} words)"
    
    meeting_keywords = ['meeting', 'discuss', 'agenda', 'action', 'will', 'should', 
                       'need', 'follow', 'deadline', 'project', 'team', 'work',
                       'task', 'complete', 'send', 'review', 'update']
    
    transcript_lower = transcript.lower()
    keyword_count = sum(1 for word in meeting_keywords if word in transcript_lower)
    
    if keyword_count < 3:
        return False, "Content doesn't seem like a meeting recording"
    
    return True, f"Valid meeting content ({word_count} words)"

def extract_action_items(transcript_text):
    """Extract action items from transcript chunk"""
    
    prompt = f"""You are an AI assistant that extracts action items from meeting transcripts.

Analyze this transcript and extract all action items. For each action item, identify:
- Who is responsible (person's name or role)
- What they need to do (the task)
- When it's due (if mentioned)

Format your response as a clean list:
- [Person/Role]: [Task] (Due: [Date/Time])

If no deadline is mentioned, write (No deadline specified).
If no specific person is mentioned, write "Team".
If there are NO action items, respond with: "NO ACTION ITEMS FOUND"

Transcript:
{transcript_text}

Action Items:"""

    try:
        response = groq_client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
            max_tokens=1000
        )
        
        return response.choices[0].message.content
    
    except Exception as e:
        return f"Error: {str(e)}"

def extract_action_items_chunked(transcript_text):
    """Extract action items from long transcript using chunking"""
    
    word_count = len(transcript_text.split())
    
    # If transcript is short enough, process directly
    if word_count < 5000:
        return extract_action_items(transcript_text)
    
    # For long transcripts, process in chunks
    st.info(f"📊 Long transcript ({word_count} words). Processing in chunks...")
    
    chunks = chunk_transcript(transcript_text, max_words=5000)
    all_action_items = []
    
    progress_bar = st.progress(0)
    for i, chunk in enumerate(chunks):
        st.write(f"Analyzing chunk {i+1}/{len(chunks)}...")
        action_items = extract_action_items(chunk)
        
        if "NO ACTION ITEMS FOUND" not in action_items:
            all_action_items.append(f"**From section {i+1}:**\n{action_items}")
        
        progress_bar.progress((i + 1) / len(chunks))
    
    if not all_action_items:
        return "NO ACTION ITEMS FOUND in any section"
    
    # Combine results
    combined = "\n\n".join(all_action_items)
    
    # Optional: Deduplicate similar items using LLM
    st.write("Consolidating results...")
    dedup_prompt = f"""Here are action items extracted from different parts of a long meeting.
Remove any duplicates and present a clean, consolidated list:

{combined}

Consolidated Action Items:"""
    
    try:
        response = groq_client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": dedup_prompt}],
            temperature=0.3,
            max_tokens=1500
        )
        return response.choices[0].message.content
    except:
        return combined  # Fallback to non-deduplicated

# UI Configuration
st.set_page_config(
    page_title="Meeting Intelligence System",
    page_icon="🎙️",
    layout="centered"
)

# Header
st.title("🎙️ Meeting Intelligence System")
st.markdown("""
Upload meeting recordings up to **200MB** (~3 hours). Supports multiple languages.
""")

# Sidebar info
with st.sidebar:
    st.header("ℹ️ Information")
    st.markdown("""
    **Supported:**
    - Audio: MP3, WAV, M4A
    - Size: Up to 200MB (~3 hours)
    - Languages: 95+ (auto-translated)
    
    **Processing Time:**
    - Short meetings (<30 min): 1-2 min
    - Long meetings (1-2 hours): 5-10 min
    - Very long (2-3 hours): 10-15 min
    
    **Note:** First use downloads Whisper model (~140MB)
    """)

# File uploader
uploaded_file = st.file_uploader(
    "Choose an audio file",
    type=['mp3', 'wav', 'm4a'],
    help="Max 200MB - Supports meetings up to 3 hours"
)

if uploaded_file is not None:
    
    # File size check
    max_size_mb = 200
    file_size_mb = uploaded_file.size / (1024 * 1024)
    
    if file_size_mb > max_size_mb:
        st.error(f"⚠️ File too large ({file_size_mb:.1f}MB). Max: {max_size_mb}MB")
        st.stop()
    
    # Save file
    file_path = UPLOAD_DIR / uploaded_file.name
    
    with open(file_path, "wb") as f:
        f.write(uploaded_file.getbuffer())
    
    st.success(f"✅ Uploaded: {uploaded_file.name}")
    st.info(f"📁 Size: {file_size_mb:.2f} MB")
    
    # Estimate processing time
    estimated_time = int(file_size_mb * 0.3)  # Rough estimate
    st.caption(f"⏱️ Estimated processing time: ~{estimated_time} minutes")
    
    # Language option
    st.markdown("---")
    language_option = st.radio(
        "Meeting language:",
        ["Auto-detect & translate to English", "English only"],
        help="Auto-detect works for 95+ languages"
    )
    
    # Transcribe button
    if st.button("🎯 Transcribe Audio", type="primary"):
        with st.spinner("Transcribing... Large files may take several minutes..."):
            try:
                model = load_model()
                
                # Transcribe (Whisper can handle long audio)
                if language_option == "Auto-detect & translate to English":
                    result = model.transcribe(str(file_path), task="translate", verbose=True)
                    st.info("🌐 Translated to English")
                else:
                    result = model.transcribe(str(file_path), verbose=True)
                
                transcript_text = result["text"]
                
                # Validate content
                is_valid, validation_message = validate_transcript(transcript_text)
                
                if not is_valid:
                    st.warning(f"⚠️ {validation_message}")
                    if not st.button("Continue Anyway"):
                        st.stop()
                else:
                    st.success(f"✅ {validation_message}")
                
                # Store transcript
                st.session_state.transcript = transcript_text
                st.session_state.filename = uploaded_file.name
                
                # Display transcript
                st.subheader("📝 Transcript")
                st.text_area("Transcribed text:", transcript_text, height=300)
                
                # Save transcript
                transcript_path = UPLOAD_DIR / f"{uploaded_file.name}.txt"
                with open(transcript_path, "w", encoding="utf-8") as f:
                    f.write(transcript_text)
                
                st.success("✅ Transcript saved!")
                
            except Exception as e:
                st.error(f"Error: {str(e)}")
                import traceback
                st.code(traceback.format_exc())
    
    # Extract action items
    if 'transcript' in st.session_state and st.session_state.get('filename') == uploaded_file.name:
        st.markdown("---")
        
        if st.button("✨ Extract Action Items", type="primary"):
            with st.spinner("Extracting action items..."):
                
                # Use chunked extraction for long transcripts
                action_items = extract_action_items_chunked(st.session_state.transcript)
                
                if "NO ACTION ITEMS FOUND" in action_items:
                    st.warning("⚠️ " + action_items)
                else:
                    st.subheader("✅ Action Items")
                    st.markdown(action_items)
                    
                    # Save
                    action_items_path = UPLOAD_DIR / f"{uploaded_file.name}_action_items.txt"
                    with open(action_items_path, "w", encoding="utf-8") as f:
                        f.write(action_items)
                    
                    st.success("✅ Saved!")
                    
                    # Download button
                    st.download_button(
                        "📥 Download Action Items",
                        action_items,
                        file_name=f"{uploaded_file.name}_action_items.txt",
                        mime="text/plain"
                    )

st.markdown("---")
st.markdown("<div style='text-align: center; color: gray; font-size: 0.8em;'>Supports meetings up to 3 hours | 95+ languages</div>", unsafe_allow_html=True)
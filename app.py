import streamlit as st
from pathlib import Path
import os
import sys
from groq import Groq
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Setup
UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)

# Initialize Groq client
groq_client = Groq(api_key=os.getenv("GROQ_API_KEY"))

# Try to import AssemblyAI (optional)
try:
    import assemblyai as aai
    aai.settings.api_key = os.getenv("ASSEMBLYAI_API_KEY")
    ASSEMBLYAI_AVAILABLE = True if os.getenv("ASSEMBLYAI_API_KEY") else False
except ImportError:
    ASSEMBLYAI_AVAILABLE = False

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
                       'task', 'complete', 'send', 'review', 'update', 'call']
    
    transcript_lower = transcript.lower()
    keyword_count = sum(1 for word in meeting_keywords if word in transcript_lower)
    
    if keyword_count < 3:
        return False, "Content doesn't seem like a meeting recording"
    
    return True, f"Valid meeting content ({word_count} words)"

def transcribe_with_groq(file_path, language_option):
    """Transcribe using Groq Whisper API - Fast & Free (up to 25MB)"""
    
    try:
        with open(file_path, "rb") as audio_file:
            if language_option == "Auto-detect & translate to English":
                # Transcribe and get language info
                transcription = groq_client.audio.transcriptions.create(
                    file=audio_file,
                    model="whisper-large-v3-turbo",
                    response_format="verbose_json"
                )
                
                # If not English, translate
                if transcription.language != "en":
                    audio_file.seek(0)
                    translation = groq_client.audio.translations.create(
                        file=audio_file,
                        model="whisper-large-v3-turbo"
                    )
                    return translation.text, transcription.language
                else:
                    return transcription.text, "en"
            else:
                transcription = groq_client.audio.transcriptions.create(
                    file=audio_file,
                    model="whisper-large-v3-turbo",
                    language="en"
                )
                return transcription.text, "en"
    
    except Exception as e:
        raise Exception(f"Groq transcription failed: {str(e)}")

def transcribe_with_assemblyai(file_path, language_option):
    """Transcribe using AssemblyAI - Handles large files (up to 5GB)"""
    
    if not ASSEMBLYAI_AVAILABLE:
        raise Exception("AssemblyAI not configured. Add ASSEMBLYAI_API_KEY to .env")
    
    try:
        transcriber = aai.Transcriber()
        
        # Configure transcription
        config = aai.TranscriptionConfig(
            language_detection=True if language_option == "Auto-detect & translate to English" else False,
            language_code="en" if language_option == "English only" else None
        )
        
        # Upload and transcribe
        transcript = transcriber.transcribe(str(file_path), config=config)
        
        # Wait for completion (AssemblyAI is async)
        if transcript.status == aai.TranscriptStatus.error:
            raise Exception(f"AssemblyAI error: {transcript.error}")
        
        detected_lang = transcript.language_code if hasattr(transcript, 'language_code') else "en"
        return transcript.text, detected_lang
    
    except Exception as e:
        raise Exception(f"AssemblyAI transcription failed: {str(e)}")

def smart_transcribe(file_path, file_size_mb, language_option, force_method=None):
    """
    Smart routing: Choose best transcription method based on file size
    
    - Small files (<20MB): Groq (fastest, free)
    - Large files (20MB-5GB): AssemblyAI (if available)
    - Fallback: User's forced choice
    """
    
    # User forced a specific method
    if force_method == "Groq":
        if file_size_mb > 25:
            raise Exception("Groq supports max 25MB. File too large!")
        return transcribe_with_groq(file_path, language_option), "Groq Whisper (Fast & Free)"
    
    elif force_method == "AssemblyAI":
        if not ASSEMBLYAI_AVAILABLE:
            raise Exception("AssemblyAI not available. Check API key in .env")
        return transcribe_with_assemblyai(file_path, language_option), "AssemblyAI (Large Files)"
    
    # Auto-routing based on file size
    else:
        # Small files: Use Groq (faster, free)
        if file_size_mb < 20:
            return transcribe_with_groq(file_path, language_option), "Groq Whisper (Auto-selected)"
        
        # Large files: Use AssemblyAI if available
        elif file_size_mb >= 20:
            if ASSEMBLYAI_AVAILABLE:
                return transcribe_with_assemblyai(file_path, language_option), "AssemblyAI (Auto-selected)"
            else:
                # No AssemblyAI, check if Groq can handle it
                if file_size_mb <= 25:
                    st.warning("⚠️ Large file. AssemblyAI not configured. Using Groq (may be slower)...")
                    return transcribe_with_groq(file_path, language_option), "Groq Whisper (Fallback)"
                else:
                    raise Exception(f"File too large ({file_size_mb:.1f}MB). Need AssemblyAI for files >25MB. Add ASSEMBLYAI_API_KEY to .env")

def generate_summary(transcript_text):
    """Generate a concise meeting summary using LLM"""
    
    # For very long transcripts, use first portion for summary
    word_count = len(transcript_text.split())
    if word_count > 3000:
        # Use first 3000 words for summary (covers main points)
        words = transcript_text.split()[:3000]
        summary_input = ' '.join(words)
        note = " (summarized from first portion of long transcript)"
    else:
        summary_input = transcript_text
        note = ""
    
    prompt = f"""You are an AI assistant that creates concise meeting summaries.

Analyze this meeting transcript and create a brief summary (3-5 sentences) that captures:
1. Main purpose/topic of the meeting
2. Key decisions made
3. Important discussion points
4. Next steps or outcomes

Keep it professional and concise. Focus on what matters most.

Transcript:
{summary_input}

Summary:"""

    try:
        response = groq_client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.5,  # Slightly higher for natural language
            max_tokens=300    # Limit summary length
        )
        
        summary = response.choices[0].message.content
        return summary + note
    
    except Exception as e:
        return f"Error generating summary: {str(e)}"

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
    
    combined = "\n\n".join(all_action_items)
    
    # Deduplicate if multiple chunks
    if len(chunks) > 1:
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
            return combined
    
    return combined

# UI Configuration
st.set_page_config(
    page_title="Meeting Intelligence System",
    page_icon="🎙️",
    layout="centered"
)

# Header
st.title("🎙️ Meeting Intelligence System")
st.markdown("""
Smart AI-powered meeting analysis: **Auto-transcription** + **Summary** + **Action Items**  
Supports 95+ languages with hybrid processing (Groq + AssemblyAI)
""")

# Sidebar
with st.sidebar:
    st.header("⚙️ Configuration")
    
    # API Status
    st.markdown("**API Status:**")
    if os.getenv("GROQ_API_KEY"):
        st.success("✅ Groq API")
    else:
        st.error("❌ Groq API (required)")
    
    if ASSEMBLYAI_AVAILABLE:
        st.success("✅ AssemblyAI (for large files)")
    else:
        st.warning("⚠️ AssemblyAI not configured")
        st.caption("Optional: Add ASSEMBLYAI_API_KEY for files >25MB")
    
    st.markdown("---")
    
    # Processing mode
    st.markdown("**Processing Mode:**")
    
    processing_options = ["🤖 Auto (Recommended)"]
    
    if os.getenv("GROQ_API_KEY"):
        processing_options.append("🚀 Groq Only (Fast, <25MB)")
    
    if ASSEMBLYAI_AVAILABLE:
        processing_options.append("🎯 AssemblyAI Only (Large files)")
    
    processing_mode = st.selectbox(
        "Choose method:",
        processing_options,
        help="Auto mode picks the best option for your file size"
    )
    
    st.markdown("---")
    
    # Info
    st.header("ℹ️ Features")
    st.markdown("""
    **New: AI Summary** ✨
    - 3-5 sentence overview
    - Key decisions highlighted
    - Main discussion points
    
    **Transcription:**
    - 🚀 Groq: Up to 25MB, fastest
    - 🎯 AssemblyAI: Up to 5GB
    - 🌐 95+ languages supported
    
    **Intelligence:**
    - Meeting summary
    - Action items extraction
    - Context-aware analysis
    """)

# File uploader
uploaded_file = st.file_uploader(
    "Choose an audio file",
    type=['mp3', 'wav', 'm4a'],
    help="Auto-routing: Small files use Groq, large files use AssemblyAI"
)

if uploaded_file is not None:
    
    # File info
    file_size_mb = uploaded_file.size / (1024 * 1024)
    
    # Save file
    file_path = UPLOAD_DIR / uploaded_file.name
    with open(file_path, "wb") as f:
        f.write(uploaded_file.getbuffer())
    
    st.success(f"✅ Uploaded: {uploaded_file.name}")
    st.info(f"📁 Size: {file_size_mb:.2f} MB")
    
    # Show which method will be used
    if "Auto" in processing_mode:
        if file_size_mb < 20:
            method_info = "🚀 Will use: **Groq** (fast & free)"
        elif file_size_mb < 25:
            method_info = "🚀 Will use: **Groq** (at size limit)"
        elif ASSEMBLYAI_AVAILABLE:
            method_info = "🎯 Will use: **AssemblyAI** (large file mode)"
        else:
            method_info = "⚠️ File too large for Groq. Need AssemblyAI!"
            st.error("Configure ASSEMBLYAI_API_KEY in .env for files >25MB")
            st.stop()
    else:
        method_info = f"Will use: **{processing_mode.split()[1]}**"
    
    st.caption(method_info)
    
    # Estimate time
    if file_size_mb < 20:
        estimated_minutes = max(1, int(file_size_mb * 0.12))
    else:
        estimated_minutes = max(1, int(file_size_mb * 0.08))
    
    st.caption(f"⏱️ Estimated time: ~{estimated_minutes} minute{'s' if estimated_minutes > 1 else ''}")
    
    # Language option
    st.markdown("---")
    language_option = st.radio(
        "Meeting language:",
        ["Auto-detect & translate to English", "English only"],
        help="Auto-detect works for 95+ languages"
    )
    
    # Transcribe button
    if st.button("🎯 Transcribe Audio", type="primary"):
        
        # Determine forced method
        if "Groq Only" in processing_mode:
            force_method = "Groq"
        elif "AssemblyAI Only" in processing_mode:
            force_method = "AssemblyAI"
        else:
            force_method = None  # Auto
        
        with st.spinner("🚀 Transcribing..."):
            try:
                # Smart transcription
                (transcript_text, detected_lang), method_used = smart_transcribe(
                    file_path, 
                    file_size_mb, 
                    language_option,
                    force_method
                )
                
                # Show which method was used
                st.success(f"✅ Transcribed using: {method_used}")
                
                if detected_lang != "en":
                    st.info(f"🌐 Language: {detected_lang.upper()} → English")
                
                # Validate content
                is_valid, validation_message = validate_transcript(transcript_text)
                
                if not is_valid:
                    st.warning(f"⚠️ {validation_message}")
                    with st.expander("📝 View Transcript"):
                        st.write(transcript_text)
                    
                    if not st.button("Continue Anyway"):
                        st.stop()
                else:
                    st.success(f"✅ {validation_message}")
                
                # Store transcript
                st.session_state.transcript = transcript_text
                st.session_state.filename = uploaded_file.name
                
                # ============= NEW: GENERATE SUMMARY =============
                st.markdown("---")
                with st.spinner("✨ Generating AI summary..."):
                    summary = generate_summary(transcript_text)
                    st.session_state.summary = summary
                
                # Display summary prominently
                st.subheader("📊 Meeting Summary")
                st.info(summary)
                # =================================================
                
                # Display transcript
                st.subheader("📝 Full Transcript")
                with st.expander("Click to view full transcript", expanded=False):
                    st.text_area("Transcribed text:", transcript_text, height=300, key="transcript_view")
                
                # Save
                transcript_path = UPLOAD_DIR / f"{uploaded_file.name}.txt"
                with open(transcript_path, "w", encoding="utf-8") as f:
                    f.write(f"MEETING SUMMARY:\n{summary}\n\n{'='*50}\n\nFULL TRANSCRIPT:\n{transcript_text}")
                
                st.download_button(
                    "📥 Download Transcript + Summary",
                    f"MEETING SUMMARY:\n{summary}\n\n{'='*50}\n\nFULL TRANSCRIPT:\n{transcript_text}",
                    file_name=f"{uploaded_file.name}_transcript.txt",
                    mime="text/plain"
                )
                
            except Exception as e:
                st.error(f"❌ Error: {str(e)}")
                
                # Help messages
                error_str = str(e).lower()
                if "api key" in error_str:
                    st.info("💡 Check your API keys in .env file")
                elif "too large" in error_str:
                    st.info("💡 Add ASSEMBLYAI_API_KEY to .env for large files")
                
                with st.expander("🔍 Details"):
                    import traceback
                    st.code(traceback.format_exc())
    
    # Extract action items
    if 'transcript' in st.session_state and st.session_state.get('filename') == uploaded_file.name:
        st.markdown("---")
        
        if st.button("✨ Extract Action Items", type="primary"):
            with st.spinner("Extracting action items..."):
                
                action_items = extract_action_items_chunked(st.session_state.transcript)
                
                if "NO ACTION ITEMS FOUND" in action_items:
                    st.warning("⚠️ " + action_items)
                else:
                    st.subheader("✅ Action Items")
                    st.markdown(action_items)
                    
                    # Store action items
                    st.session_state.action_items = action_items
                    
                    # Save complete report
                    summary = st.session_state.get('summary', 'No summary generated')
                    complete_report = f"""MEETING ANALYSIS REPORT
{'='*50}

📊 SUMMARY:
{summary}

{'='*50}

✅ ACTION ITEMS:
{action_items}

{'='*50}

📝 FULL TRANSCRIPT:
{st.session_state.transcript}
"""
                    
                    action_items_path = UPLOAD_DIR / f"{uploaded_file.name}_complete_report.txt"
                    with open(action_items_path, "w", encoding="utf-8") as f:
                        f.write(complete_report)
                    
                    st.download_button(
                        "📥 Download Complete Report",
                        complete_report,
                        file_name=f"{uploaded_file.name}_complete_report.txt",
                        mime="text/plain"
                    )

# Footer
st.markdown("---")
st.markdown("""
<div style='text-align: center; color: gray; font-size: 0.8em;'>
✨ AI-Powered Meeting Intelligence | Summary + Action Items + Transcription
</div>
""", unsafe_allow_html=True)

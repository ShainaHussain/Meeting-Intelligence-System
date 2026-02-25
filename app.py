import streamlit as st
from pathlib import Path
import os
from groq import Groq

# ── API Key Resolution ────────────────────────────────────────────────────────
# Priority: st.secrets (HF Spaces) → env var → user input in sidebar
def get_secret(key: str):
    try:
        return st.secrets[key]
    except Exception:
        return os.getenv(key)

# ── Setup ─────────────────────────────────────────────────────────────────────
UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)

try:
    import assemblyai as aai
    ASSEMBLYAI_INSTALLED = True
except ImportError:
    ASSEMBLYAI_INSTALLED = False

# ── Helpers ───────────────────────────────────────────────────────────────────
def chunk_transcript(text, max_words=5000):
    words = text.split()
    return [" ".join(words[i : i + max_words]) for i in range(0, len(words), max_words)]


def validate_transcript(transcript):
    word_count = len(transcript.split())
    if word_count < 50:
        return False, f"Transcript too short ({word_count} words)"
    meeting_keywords = [
        "meeting", "discuss", "agenda", "action", "will", "should",
        "need", "follow", "deadline", "project", "team", "work",
        "task", "complete", "send", "review", "update", "call",
    ]
    keyword_count = sum(1 for w in meeting_keywords if w in transcript.lower())
    if keyword_count < 3:
        return False, "Content doesn't seem like a meeting recording"
    return True, f"Valid meeting content ({word_count} words)"


# ── Transcription ─────────────────────────────────────────────────────────────
def transcribe_with_groq(file_path, language_option, client):
    with open(file_path, "rb") as audio_file:
        if language_option == "Auto-detect & translate to English":
            transcription = client.audio.transcriptions.create(
                file=audio_file,
                model="whisper-large-v3-turbo",
                response_format="verbose_json",
            )
            if transcription.language != "en":
                audio_file.seek(0)
                translation = client.audio.translations.create(
                    file=audio_file, model="whisper-large-v3-turbo"
                )
                return translation.text, transcription.language
            return transcription.text, "en"
        else:
            transcription = client.audio.transcriptions.create(
                file=audio_file, model="whisper-large-v3-turbo", language="en"
            )
            return transcription.text, "en"


def transcribe_with_assemblyai(file_path, language_option, api_key):
    aai.settings.api_key = api_key
    config = aai.TranscriptionConfig(
        language_detection=(language_option == "Auto-detect & translate to English"),
        language_code="en" if language_option == "English only" else None,
    )
    transcriber = aai.Transcriber()
    transcript = transcriber.transcribe(str(file_path), config=config)
    if transcript.status == aai.TranscriptStatus.error:
        raise Exception(f"AssemblyAI error: {transcript.error}")
    detected_lang = getattr(transcript, "language_code", "en")
    return transcript.text, detected_lang


def smart_transcribe(file_path, file_size_mb, language_option, groq_key, assemblyai_key, force_method=None):
    assemblyai_available = ASSEMBLYAI_INSTALLED and bool(assemblyai_key)
    client = Groq(api_key=groq_key)

    if force_method == "Groq":
        if file_size_mb > 25:
            raise Exception("Groq supports max 25 MB. File too large.")
        return transcribe_with_groq(file_path, language_option, client), "Groq Whisper (Fast & Free)"

    if force_method == "AssemblyAI":
        if not assemblyai_available:
            raise Exception("AssemblyAI not available. Check your API key.")
        return transcribe_with_assemblyai(file_path, language_option, assemblyai_key), "AssemblyAI (Large Files)"

    # Auto-routing
    if file_size_mb < 20:
        return transcribe_with_groq(file_path, language_option, client), "Groq Whisper (Auto-selected)"

    if assemblyai_available:
        return transcribe_with_assemblyai(file_path, language_option, assemblyai_key), "AssemblyAI (Auto-selected)"

    if file_size_mb <= 25:
        st.warning("Large file. AssemblyAI not configured. Using Groq (may be slower)…")
        return transcribe_with_groq(file_path, language_option, client), "Groq Whisper (Fallback)"

    raise Exception(f"File too large ({file_size_mb:.1f} MB). Add an AssemblyAI API key for files > 25 MB.")


# ── LLM Intelligence ──────────────────────────────────────────────────────────
def generate_summary(transcript_text, client):
    words = transcript_text.split()
    summary_input = " ".join(words[:3000]) if len(words) > 3000 else transcript_text
    note = " *(summarized from first portion of long transcript)*" if len(words) > 3000 else ""

    prompt = f"""You are an AI assistant that creates concise meeting summaries.

Analyze this meeting transcript and create a brief summary (3-5 sentences) that captures:
1. Main purpose/topic of the meeting
2. Key decisions made
3. Important discussion points
4. Next steps or outcomes

Keep it professional and concise.

Transcript:
{summary_input}

Summary:"""

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.5,
        max_tokens=300,
    )
    return response.choices[0].message.content + note


def extract_action_items(transcript_text, client):
    prompt = f"""You are an AI assistant that extracts action items from meeting transcripts.

Extract all action items. For each, identify:
- Who is responsible (name or role)
- What they need to do
- When it's due (if mentioned)

Format:
- [Person/Role]: [Task] (Due: [Date/Time])

If no deadline: write (No deadline specified).
If no person: write "Team".
If NO action items exist: respond with "NO ACTION ITEMS FOUND"

Transcript:
{transcript_text}

Action Items:"""

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.3,
        max_tokens=1000,
    )
    return response.choices[0].message.content


def extract_action_items_chunked(transcript_text, client):
    word_count = len(transcript_text.split())
    if word_count < 5000:
        return extract_action_items(transcript_text, client)

    st.info(f"📊 Long transcript ({word_count} words). Processing in chunks…")
    chunks = chunk_transcript(transcript_text)
    all_items = []

    progress_bar = st.progress(0)
    for i, chunk in enumerate(chunks):
        st.write(f"Analyzing chunk {i + 1}/{len(chunks)}…")
        items = extract_action_items(chunk, client)
        if "NO ACTION ITEMS FOUND" not in items:
            all_items.append(f"**From section {i + 1}:**\n{items}")
        progress_bar.progress((i + 1) / len(chunks))

    if not all_items:
        return "NO ACTION ITEMS FOUND in any section"

    combined = "\n\n".join(all_items)
    if len(chunks) > 1:
        st.write("Consolidating results…")
        dedup_prompt = f"""Deduplicate and consolidate this action items list into one clean list:

{combined}

Consolidated Action Items:"""
        try:
            response = client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[{"role": "user", "content": dedup_prompt}],
                temperature=0.3,
                max_tokens=1500,
            )
            return response.choices[0].message.content
        except Exception:
            return combined
    return combined


# ── UI ────────────────────────────────────────────────────────────────────────
st.set_page_config(page_title="Meeting Intelligence System", page_icon="🎙️", layout="centered")

st.title("🎙️ Meeting Intelligence System")
st.markdown(
    "AI-powered meeting analysis: **Auto-transcription** + **Summary** + **Action Items**  \n"
    "Supports 95+ languages · Powered by Groq Whisper + Llama 3.3"
)

# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.header("⚙️ Configuration")
    st.markdown("**API Keys**")

    groq_key = get_secret("GROQ_API_KEY") or st.text_input(
        "Groq API Key", type="password", help="Free key at console.groq.com"
    )
    assemblyai_key = get_secret("ASSEMBLYAI_API_KEY") or st.text_input(
        "AssemblyAI Key (optional)", type="password", help="Only needed for files > 25 MB"
    )

    st.markdown("---")
    st.markdown("**API Status:**")
    if groq_key:
        st.success("✅ Groq API")
    else:
        st.error("❌ Groq API key required")

    assemblyai_available = ASSEMBLYAI_INSTALLED and bool(assemblyai_key)
    if assemblyai_available:
        st.success("✅ AssemblyAI (large files)")
    else:
        st.warning("⚠️ AssemblyAI not configured")
        st.caption("Optional: for files > 25 MB")

    st.markdown("---")
    st.markdown("**Processing Mode:**")
    processing_options = ["🤖 Auto (Recommended)"]
    if groq_key:
        processing_options.append("🚀 Groq Only (Fast, <25MB)")
    if assemblyai_available:
        processing_options.append("🎯 AssemblyAI Only (Large files)")

    processing_mode = st.selectbox("Choose method:", processing_options)

    st.markdown("---")
    st.header("ℹ️ Features")
    st.markdown("""
    **Summary** ✨ — 3-5 sentence overview
    
    **Transcription:**
    - 🚀 Groq: Up to 25 MB, fastest
    - 🎯 AssemblyAI: Up to 5 GB
    - 🌐 95+ languages

    **Intelligence:**
    - Meeting summary
    - Action item extraction
    """)
    st.markdown("---")
    st.caption("⚠️ Files are stored temporarily and deleted when the session ends.")

# ── Guard: require Groq key ───────────────────────────────────────────────────
if not groq_key:
    st.warning("👈 Enter your Groq API key in the sidebar to get started.")
    st.info("Get a **free** key at [console.groq.com](https://console.groq.com)")
    st.stop()

# ── Upload ────────────────────────────────────────────────────────────────────
uploaded_file = st.file_uploader(
    "Choose an audio file",
    type=["mp3", "wav", "m4a"],
    help="Small files → Groq · Large files → AssemblyAI",
)

if uploaded_file is not None:
    file_size_mb = uploaded_file.size / (1024 * 1024)

    file_path = UPLOAD_DIR / uploaded_file.name
    with open(file_path, "wb") as f:
        f.write(uploaded_file.getbuffer())

    st.success(f"✅ Uploaded: **{uploaded_file.name}**")
    st.info(f"📁 Size: {file_size_mb:.2f} MB")

    # Routing info
    if "Auto" in processing_mode:
        if file_size_mb < 20:
            st.caption("🚀 Will use: **Groq** (fast & free)")
        elif file_size_mb <= 25:
            st.caption("🚀 Will use: **Groq** (near size limit)")
        elif assemblyai_available:
            st.caption("🎯 Will use: **AssemblyAI** (large file mode)")
        else:
            st.error("File too large for Groq (> 25 MB). Add an AssemblyAI key in the sidebar.")
            st.stop()
    else:
        st.caption(f"Will use: **{processing_mode.split()[1]}**")

    estimated_minutes = max(1, int(file_size_mb * (0.12 if file_size_mb < 20 else 0.08)))
    st.caption(f"⏱️ Estimated time: ~{estimated_minutes} minute{'s' if estimated_minutes > 1 else ''}")

    st.markdown("---")
    language_option = st.radio(
        "Meeting language:",
        ["Auto-detect & translate to English", "English only"],
    )

    if st.button("🎯 Transcribe Audio", type="primary"):
        force_method = (
            "Groq" if "Groq Only" in processing_mode
            else "AssemblyAI" if "AssemblyAI Only" in processing_mode
            else None
        )

        with st.spinner("🚀 Transcribing…"):
            try:
                (transcript_text, detected_lang), method_used = smart_transcribe(
                    file_path, file_size_mb, language_option,
                    groq_key, assemblyai_key if assemblyai_available else None, force_method,
                )

                st.success(f"✅ Transcribed using: {method_used}")
                if detected_lang != "en":
                    st.info(f"🌐 Detected: **{detected_lang.upper()}** → translated to English")

                is_valid, msg = validate_transcript(transcript_text)
                if not is_valid:
                    st.warning(f"⚠️ {msg}")
                    with st.expander("📝 View Transcript Anyway"):
                        st.write(transcript_text)
                else:
                    st.success(f"✅ {msg}")

                st.session_state.transcript = transcript_text
                st.session_state.filename = uploaded_file.name

                st.markdown("---")
                client = Groq(api_key=groq_key)
                with st.spinner("✨ Generating AI summary…"):
                    summary = generate_summary(transcript_text, client)
                    st.session_state.summary = summary

                st.subheader("📊 Meeting Summary")
                st.info(summary)

                st.subheader("📝 Full Transcript")
                with st.expander("Click to view full transcript", expanded=False):
                    st.text_area("Transcribed text:", transcript_text, height=300, key="transcript_view")

                download_content = (
                    f"MEETING SUMMARY:\n{summary}\n\n{'='*50}\n\nFULL TRANSCRIPT:\n{transcript_text}"
                )
                st.download_button(
                    "📥 Download Transcript + Summary",
                    download_content,
                    file_name=f"{uploaded_file.name}_transcript.txt",
                    mime="text/plain",
                )

            except Exception as e:
                st.error(f"❌ Error: {str(e)}")
                error_str = str(e).lower()
                if "api key" in error_str or "authentication" in error_str:
                    st.info("💡 Double-check your API key in the sidebar.")
                elif "too large" in error_str:
                    st.info("💡 Add an AssemblyAI key in the sidebar for large files.")
                with st.expander("🔍 Full error details"):
                    import traceback
                    st.code(traceback.format_exc())

    # Action items — only show after transcription
    if (
        "transcript" in st.session_state
        and st.session_state.get("filename") == uploaded_file.name
    ):
        st.markdown("---")
        if st.button("✨ Extract Action Items", type="primary"):
            with st.spinner("Extracting action items…"):
                try:
                    client = Groq(api_key=groq_key)
                    action_items = extract_action_items_chunked(st.session_state.transcript, client)

                    if "NO ACTION ITEMS FOUND" in action_items:
                        st.warning("⚠️ " + action_items)
                    else:
                        st.subheader("✅ Action Items")
                        st.markdown(action_items)
                        st.session_state.action_items = action_items

                        summary = st.session_state.get("summary", "No summary generated")
                        complete_report = (
                            f"MEETING ANALYSIS REPORT\n{'='*50}\n\n"
                            f"SUMMARY:\n{summary}\n\n{'='*50}\n\n"
                            f"ACTION ITEMS:\n{action_items}\n\n{'='*50}\n\n"
                            f"FULL TRANSCRIPT:\n{st.session_state.transcript}\n"
                        )
                        st.download_button(
                            "📥 Download Complete Report",
                            complete_report,
                            file_name=f"{uploaded_file.name}_complete_report.txt",
                            mime="text/plain",
                        )
                except Exception as e:
                    st.error(f"❌ Error extracting action items: {str(e)}")
# ── Footer ────────────────────────────────────────────────────────────────────
st.markdown("---")
st.markdown(
    "<div style='text-align:center;color:gray;font-size:0.8em;'>"
    "✨ Meeting Intelligence System · Built by "
    "<a href='https://github.com/ShainaHussain' target='_blank'>Shaina Hussain</a>"
    "</div>",
    unsafe_allow_html=True,
)
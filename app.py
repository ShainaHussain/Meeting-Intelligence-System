import streamlit as st
from pathlib import Path
import whisper
import os
import sys

# Setup
UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)

# Find FFmpeg in Anaconda
if sys.platform == "win32":
    # Get Anaconda base path
    conda_base = Path(sys.executable).parent
    ffmpeg_path = conda_base / "Library" / "bin" / "ffmpeg.exe"
    
    if ffmpeg_path.exists():
        # Add to PATH so Whisper can find it
        os.environ["PATH"] = str(ffmpeg_path.parent) + os.pathsep + os.environ["PATH"]
        st.sidebar.success("✅ FFmpeg found")
    else:
        st.sidebar.warning(f"⚠️ FFmpeg not found at {ffmpeg_path}")

# Load Whisper model (only once)
@st.cache_resource
def load_model():
    return whisper.load_model("base")

# UI
st.title("🎙️ Meeting Intelligence System")
st.markdown("Upload your meeting recording to extract action items")

# File uploader
uploaded_file = st.file_uploader(
    "Choose an audio file",
    type=['mp3', 'wav', 'm4a']
)

# Handle upload
if uploaded_file is not None:
    # Save file
    file_path = UPLOAD_DIR / uploaded_file.name
    
    with open(file_path, "wb") as f:
        f.write(uploaded_file.getbuffer())
    
    st.success(f"✅ File uploaded: {uploaded_file.name}")
    st.info(f"📁 File size: {uploaded_file.size / 1024:.1f} KB")
    
    # Debug info
    st.write(f"**Debug:** File path: {file_path}")
    st.write(f"**Debug:** File exists? {file_path.exists()}")
    
    # Transcribe button
    if st.button("🎯 Transcribe Audio"):
        with st.spinner("Transcribing... This may take a minute..."):
            try:
                # Load model
                model = load_model()
                
                # Transcribe
                result = model.transcribe(str(file_path))
                transcript_text = result["text"]
                
                # Display transcript
                st.subheader("📝 Transcript")
                st.write(transcript_text)
                
                # Save transcript
                transcript_path = UPLOAD_DIR / f"{uploaded_file.name}.txt"
                with open(transcript_path, "w", encoding="utf-8") as f:
                    f.write(transcript_text)
                
                st.success(f"✅ Transcript saved!")
                
            except Exception as e:
                st.error(f"Error during transcription: {str(e)}")
                import traceback
                st.code(traceback.format_exc())
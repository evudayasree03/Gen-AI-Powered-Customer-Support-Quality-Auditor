import os
import re
import whisper
import streamlit as st
from groq import Groq
from dotenv import load_dotenv

# -----------------------------
# Load API Key
# -----------------------------
load_dotenv()
groq_api_key = os.getenv("GROQ_API_KEY")

if not groq_api_key:
    st.error("GROQ_API_KEY not found in .env file")
    st.stop()

client = Groq(api_key=groq_api_key)

# -----------------------------
# Chunked Summarization
# -----------------------------
def summarize_text(text, chunk_size=8000):

    chunks = [text[i:i + chunk_size] for i in range(0, len(text), chunk_size)]
    st.info(f"Text split into {len(chunks)} chunk(s).")

    chunk_summaries = []

    for idx, chunk in enumerate(chunks):
        with st.spinner(f"Summarizing chunk {idx + 1}/{len(chunks)}..."):
            response = client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[
                    {
                        "role": "system",
                        "content": """Summarize clearly and concisely.
Only provide the final summary.
Do NOT include reasoning or thoughts."""
                    },
                    {
                        "role": "user",
                        "content": chunk
                    }
                ],
                temperature=0.3
            )

            summary = response.choices[0].message.content
            summary = re.sub(r"<think>.*?</think>", "", summary, flags=re.DOTALL).strip()
            chunk_summaries.append(summary)

    if len(chunk_summaries) == 1:
        return chunk_summaries[0]

    combined_summary = "\n".join(chunk_summaries)

    with st.spinner("Generating final consolidated summary..."):
        final_response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {
                    "role": "system",
                    "content": "Create a final concise summary from the following summaries and you must include the participants in the conversation."
                },
                {
                    "role": "user",
                    "content": combined_summary
                }
            ],
            temperature=0.3
        )

        final_summary = final_response.choices[0].message.content
        final_summary = re.sub(r"<think>.*?</think>", "", final_summary, flags=re.DOTALL).strip()

    return final_summary


# -----------------------------
# Streamlit UI
# -----------------------------
st.set_page_config(page_title="Transcription & Summarization App", layout="centered")

st.title("🎙 Audio & 📄 Text Summarizer")
st.write("Upload an audio file (.mp3, .wav, .m4a) or a text file (.txt) to generate a summary.")

uploaded_file = st.file_uploader("Upload File", type=["mp3", "wav", "m4a", "txt"])

if uploaded_file is not None:

    file_extension = os.path.splitext(uploaded_file.name)[1].lower()

    # Save uploaded file temporarily
    with open(uploaded_file.name, "wb") as f:
        f.write(uploaded_file.getbuffer())

    # AUDIO FILE
    if file_extension in [".mp3", ".wav", ".m4a"]:
        st.info("Audio detected. Transcribing...")
        model = whisper.load_model("base")
        result = model.transcribe(uploaded_file.name)
        text = result["text"]

        #st.subheader("Transcript")
        #st.write(text)

    # TEXT FILE
    elif file_extension == ".txt":
        st.info("Text file detected. Reading...")
        text = uploaded_file.read().decode("utf-8")

    else:
        st.error("Unsupported file type.")
        st.stop()

    # Generate Summary
    st.subheader("Generating Summary...")
    summary = summarize_text(text)

    st.subheader("📌 Final Summary")
    st.write(summary)

    # Download button
    st.download_button(
        label="Download Summary",
        data=summary,
        file_name="summary.txt",
        mime="text/plain"
    )
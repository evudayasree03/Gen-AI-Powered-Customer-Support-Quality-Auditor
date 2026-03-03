import os
import re
import tempfile
import streamlit as st
import pandas as pd
import plotly.express as px
from groq import Groq
from dotenv import load_dotenv
from deepgram import DeepgramClient
from scoring_schema import SCORING_SYSTEM_PROMPT, parse_scoring_output
from db import save_call, get_calls

# -----------------------------
# Load API Keys
# -----------------------------
load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
DEEPGRAM_API_KEY = os.getenv("DEEPGRAM_API_KEY")

groq_client = Groq(api_key=GROQ_API_KEY)

# -----------------------------
# Page Config
# -----------------------------
st.set_page_config(
    page_title="SamiX - GenAI Customer Support QA Platform",
    page_icon="🎧",
    layout="wide"
)

# -----------------------------
# Sidebar Navigation
# -----------------------------
st.sidebar.title("🎧 GenAI Customer Support QA Platform")

menu = st.sidebar.radio(
    "Navigation",
    [
        "Upload Logs",
        "Conversation Summary",
        "Quality Dashboard",
        "Call History"
    ]
)

st.sidebar.markdown("---")

st.sidebar.markdown("### Features")
st.sidebar.write("• Speech Transcription")
st.sidebar.write("• AI Call Summarization")
st.sidebar.write("• QA Scoring Engine")
st.sidebar.write("• Conversation Analytics")

st.title("SamiX - GenAI Customer Support QA Platform")
# -----------------------------
# Deepgram Transcription
# -----------------------------
def transcribe_with_deepgram(file_path, max_pause=0.8):

    deepgram_client = DeepgramClient(api_key=DEEPGRAM_API_KEY)

    with open(file_path, "rb") as f:
        audio_bytes = f.read()

    response = deepgram_client.listen.v1.media.transcribe_file(
        request=audio_bytes,
        model="nova-2",
        smart_format=True,
        diarize=True
    )

    words = response.results.channels[0].alternatives[0].words

    first_word_time = words[0].start
    last_word_time = words[-1].end
    call_duration = last_word_time - first_word_time

    transcript_lines = []
    current_speaker = None
    current_line = []
    last_end_time = None

    for word_info in words:

        speaker = word_info.speaker
        word = word_info.word
        start_time = word_info.start
        end_time = word_info.end

        if speaker != current_speaker or (
            last_end_time is not None and start_time - last_end_time > max_pause
        ):

            if current_line:
                transcript_lines.append(
                    f"Speaker {current_speaker}: {' '.join(current_line)}"
                )

            current_speaker = speaker
            current_line = [word]

        else:
            current_line.append(word)

        last_end_time = end_time

    if current_line:
        transcript_lines.append(
            f"Speaker {current_speaker}: {' '.join(current_line)}"
        )

    transcript = "\n".join(transcript_lines)

    return transcript, call_duration


def format_duration(seconds):

    minutes = int(seconds // 60)
    seconds = int(seconds % 60)

    return f"{minutes}:{seconds:02d}"


# -----------------------------
# Summarization
# -----------------------------
def summarize_text(text, chunk_size=8000):

    chunks = [text[i:i + chunk_size] for i in range(0, len(text), chunk_size)]

    summaries = []

    for chunk in chunks:

        response = groq_client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": "Summarize the conversation clearly."},
                {"role": "user", "content": chunk}
            ],
            temperature=0.3
        )

        summary = response.choices[0].message.content
        summary = re.sub(r"<think>.*?</think>", "", summary)

        summaries.append(summary)

    return "\n".join(summaries)


# -----------------------------
# QA Scoring
# -----------------------------
def score_conversation(text):

    response = groq_client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {"role": "system", "content": SCORING_SYSTEM_PROMPT},
            {"role": "user", "content": text[:8000]}
        ],
        temperature=0.2
    )

    raw = response.choices[0].message.content

    return parse_scoring_output(raw)


# -----------------------------
# Session State
# -----------------------------
if "transcript" not in st.session_state:
    st.session_state.transcript = None

if "summary" not in st.session_state:
    st.session_state.summary = None

if "duration" not in st.session_state:
    st.session_state.duration = None

if "scores" not in st.session_state:
    st.session_state.scores = None

if "filename" not in st.session_state:
    st.session_state.filename = None


# -----------------------------
# Score Card UI
# -----------------------------
def score_card(title, score, justification):

    color = "#22c55e" if score >= 4 else "#f59e0b" if score == 3 else "#ef4444"

    st.markdown(
        f"""
        <div style="
            background:#0f172a;
            padding:16px;
            border-radius:12px;
            border-left:6px solid {color};
            min-height:160px;
        ">
        <h4 style="margin-bottom:6px">{title}</h4>
        <h2 style="margin-top:0">{score}/5</h2>
        <p style="font-size:13px;color:#cbd5f5;">
        {justification}
        </p>
        </div>
        """,
        unsafe_allow_html=True
    )


# -----------------------------
# PAGE 1: Upload Logs
# -----------------------------
if menu == "Upload Logs":

    st.header("📂 Upload Conversation Logs")

    uploaded_file = st.file_uploader(
        "Upload audio (.mp3, .wav, .m4a) or transcript (.txt)",
        type=["mp3", "wav", "m4a", "txt"]
    )

    if uploaded_file:

        ext = os.path.splitext(uploaded_file.name)[1].lower()

        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            tmp.write(uploaded_file.getbuffer())
            file_path = tmp.name

        if ext in [".mp3", ".wav", ".m4a"]:

            st.info("Transcribing audio...")

            transcript, duration = transcribe_with_deepgram(file_path)

        else:

            transcript = uploaded_file.read().decode("utf-8")
            duration = None

        st.session_state.transcript = transcript
        st.session_state.duration = duration
        st.session_state.summary = None
        st.session_state.scores = None
        st.session_state.filename = uploaded_file.name

        st.success("Transcription Complete")

        st.text_area("Transcript", transcript, height=400)


# -----------------------------
# PAGE 2: Conversation Summary
# -----------------------------
elif menu == "Conversation Summary":

    st.title("📄 AI Conversation Summary")

    if not st.session_state.transcript:

        st.warning("Upload logs first.")

    else:

        if not st.session_state.summary:

            with st.spinner("Generating summary..."):

                st.session_state.summary = summarize_text(
                    st.session_state.transcript
                )

        st.info(st.session_state.summary)

        st.download_button(
            "Download Summary",
            st.session_state.summary,
            "summary.txt"
        )

        if st.session_state.duration:

            st.metric(
                "Call Duration",
                format_duration(st.session_state.duration)
            )


# -----------------------------
# PAGE 3: Quality Dashboard
# -----------------------------
elif menu == "Quality Dashboard":

    st.title("📊 Support Quality Dashboard")

    if not st.session_state.transcript:

        st.warning("Upload logs first.")

    else:

        if not st.session_state.scores:

            with st.spinner("Evaluating conversation..."):

                st.session_state.scores = score_conversation(
                    st.session_state.transcript
                )

                save_call(
                    st.session_state.filename,
                    st.session_state.transcript,
                    st.session_state.summary,
                    st.session_state.scores,
                    format_duration(st.session_state.duration)
                    if st.session_state.duration else "N/A"
                )

        scores = st.session_state.scores

        overall = (
            scores["Customer Satisfaction"]["score"]
            + scores["Empathy"]["score"]
            + scores["Issue Resolution"]["score"]
            + scores["Communication Quality"]["score"]
            + scores["Compliance & Bias"]["score"]
        ) / 5

        st.markdown("### ⭐ Overall Quality Score")
        st.progress(int(overall * 20))
        st.markdown(f"### {overall:.1f} / 5")

        cols = st.columns(5)

        metrics = [
            ("Satisfaction", "Customer Satisfaction"),
            ("Empathy", "Empathy"),
            ("Resolution", "Issue Resolution"),
            ("Communication", "Communication Quality"),
            ("Compliance", "Compliance & Bias"),
        ]

        for col, (label, key) in zip(cols, metrics):

            with col:
                score_card(
                    label,
                    scores[key]["score"],
                    scores[key]["justification"]
                )

        radar_df = pd.DataFrame({
            "Metric": [
                "Satisfaction",
                "Empathy",
                "Resolution",
                "Communication",
                "Compliance"
            ],
            "Score": [
                scores["Customer Satisfaction"]["score"],
                scores["Empathy"]["score"],
                scores["Issue Resolution"]["score"],
                scores["Communication Quality"]["score"],
                scores["Compliance & Bias"]["score"]
            ]
        })

        fig = px.line_polar(
            radar_df,
            r="Score",
            theta="Metric",
            line_close=True,
            range_r=[0, 5]
        )

        fig.update_traces(fill="toself")

        st.plotly_chart(fig, use_container_width=True)

        col1, col2 = st.columns(2)

        with col1:

            st.success("Strengths")

            for s in scores["strengths"]:
                st.write("✅", s)

        with col2:

            st.warning("Improvements")

            for i in scores["improvements"]:
                st.write("⚠", i)


# -----------------------------
# PAGE 4: Call History
# -----------------------------
elif menu == "Call History":

    st.title("📂 Analyzed Calls History")

    calls = get_calls()

    df = pd.DataFrame(
        calls,
        columns=[
            "ID",
            "File Name",
            "Transcript",
            "Summary",
            "Scores",
            "Duration",
            "Timestamp"
        ]
    )

    # Show only summary info in table
    st.dataframe(df[["ID", "File Name", "Duration", "Timestamp"]])

    st.markdown("### Select a Call")

    selected = st.selectbox("Call ID", df["ID"])

    call = df[df["ID"] == selected].iloc[0]

    if st.button("View Transcript"):

        with st.expander("Transcript Viewer"):

            st.subheader("Full Transcript")

            st.text_area( 
                "Transcript",
                call["Transcript"],
                height=400
            )

            st.subheader("Summary")

            st.write(call["Summary"])

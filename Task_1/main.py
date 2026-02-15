import os
import re
import whisper
from groq import Groq
from dotenv import load_dotenv

# -----------------------------
# Loading API Key
# -----------------------------
load_dotenv()
groq_api_key = os.getenv("GROQ_API_KEY")

if not groq_api_key:
    raise ValueError("GROQ_API_KEY not found in .env file")

client = Groq(api_key=groq_api_key)

# -----------------------------
# Chunked Summarization Function
# -----------------------------
def summarize_text(text, chunk_size=8000):

    # Split text into safe-size chunks
    chunks = [text[i:i + chunk_size] for i in range(0, len(text), chunk_size)]
    print(f"Text split into {len(chunks)} chunk(s).")

    chunk_summaries = []

    for idx, chunk in enumerate(chunks):
        print(f"Summarizing chunk {idx + 1}/{len(chunks)}")

        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {
                    "role": "system",
                    "content": """Summarize clearly and concisely.
provide the final summary.You must include the participants in the conversation.
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

    # If only one chunk, return directly
    if len(chunk_summaries) == 1:
        return chunk_summaries[0]

    # Combine summaries
    combined_summary = "\n".join(chunk_summaries)

    print("Generating final consolidated summary...")

    final_response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {
                "role": "system",
                "content": "Create a final concise summary from the following summaries and you must include the participants in the conversation. "
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
# Processing the File
# -----------------------------
def process_file(file_path):

    file_extension = os.path.splitext(file_path)[1].lower()

    # 🎙 Audio files
    if file_extension in [".mp3", ".wav", ".m4a"]:
        print("Audio detected. Transcribing...")
        model = whisper.load_model("base")
        result = model.transcribe(file_path)
        text = result["text"]

        with open("transcript.txt", "w", encoding="utf-8") as f:
            f.write(text)

        print("Transcript saved as transcript.txt")

    # 📄 Text files
    elif file_extension == ".txt":
        print("Text file detected. Reading...")
        with open(file_path, "r", encoding="utf-8") as f:
            text = f.read()

    else:
        raise ValueError("Unsupported file type. Only audio (.mp3, .wav, .m4a) and .txt allowed.")

    # -----------------------------
    # Summarization (with chunking)
    # -----------------------------
    print("Generating summary...")
    summary = summarize_text(text)

    with open("summary.txt", "w", encoding="utf-8") as f:
        f.write(summary)

    print("\n--- FINAL SUMMARY ---\n")
    print(summary)


# -----------------------------
# Run
# -----------------------------
if __name__ == "__main__":
    file_name = input("Enter file name (with extension): ")
    process_file(file_name)
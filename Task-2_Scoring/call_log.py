import asyncio
import edge_tts
from pydub import AudioSegment
from io import BytesIO

# Voices
agent_voice = "en-US-GuyNeural"
customer_voice = "en-US-JennyNeural"

# Read transcript
with open("chat.txt", "r", encoding="utf-8") as f:
    lines = f.readlines()

dialogue = []

for line in lines:

    line = line.strip()

    if not line:
        continue

    if line.startswith("Speaker 0:"):
        text = line.replace("Speaker 0:", "").strip()
        dialogue.append((text, agent_voice))

    elif line.startswith("Speaker 1:"):
        text = line.replace("Speaker 1:", "").strip()
        dialogue.append((text, customer_voice))


async def generate_call():

    combined = AudioSegment.empty()
    pause = AudioSegment.silent(duration=600)

    for text, voice in dialogue:

        communicate = edge_tts.Communicate(text=text, voice=voice)

        audio_bytes = b""

        async for chunk in communicate.stream():
            if chunk["type"] == "audio":
                audio_bytes += chunk["data"]

        segment = AudioSegment.from_file(BytesIO(audio_bytes), format="mp3")

        combined += segment + pause

    # simulate phone audio quality
    combined = combined.set_frame_rate(8000).set_channels(1)

    combined.export("call_recording.wav", format="wav")


asyncio.run(generate_call())

print("Call recording created: call_recording.wav")
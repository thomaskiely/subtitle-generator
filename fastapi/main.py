from fastapi import FastAPI, File, UploadFile, Form
from fastapi.responses import StreamingResponse
import subprocess
from io import BytesIO
from fastapi.middleware.cors import CORSMiddleware
import whisper
from pydub import AudioSegment
import numpy as np
import shutil
import os
import asyncio
import logging

app = FastAPI()
logger = logging.getLogger()

model = whisper.load_model("base")

# Allow CORS from specific origins (like your React app's port)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # React app's address
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods (GET, POST, etc.)
    allow_headers=["*"],  # Allows all headers
)

@app.post("/generate-subtitles")
async def subtitleEndpoint(file: UploadFile=File(...), font: str=Form(...)):
    logger.info('generating subtitles...')

    #process input file
    file_content = await file.read()
    audio = AudioSegment.from_file(BytesIO(file_content))
    if audio.channels > 1:
        audio = audio.set_channels(1)
    audio = audio.set_frame_rate(16000)
    samples = np.array(audio.get_array_of_samples(), dtype=np.float32)
    samples /= np.max(np.abs(samples))
    
    #call whisper to grab the timestamp/duration of each word
    word_timestamps = speechToText(samples)

    #convert the timestamps to an SRT file
    generate_srt(word_timestamps, "output_captions.srt")

    #save the uploaded mp4 to disk
    save_upload_file(file, "output_video.mp4")

    #run the ffmpeg command on the uploaded mp4 file with the srt file
    await add_subtitles()

    def file_streamer(file_path):
        with open(file_path, "rb") as file:
            yield from file

    response = StreamingResponse(file_streamer("generated.mp4"), media_type="video/mp4")
    return response   
    

def save_upload_file(upload_file: UploadFile, dest_path: str):
    """Saves an UploadFile to a given file path."""
    upload_file.file.seek(0)
    with open(dest_path, "wb") as buffer:
        shutil.copyfileobj(upload_file.file, buffer)

def speechToText(audio):
    """
    Converts speech from an audio file to text, providing word-level timestamps.

    Uses OpenAI's Whisper model to transcribe the given audio file, and returns a list of words with their respective start and end timestamps.

    Parameters:
    audio (str or Path): The audio file (in a compatible format) to be transcribed.

    Returns:
    list of tuples: A list where each tuple contains a word, its start time, and its end time in the transcription.
                    Example: [("hello", 0.0, 0.5), ("world", 0.6, 1.2)]
    
    Note:
    - This function assumes that the Whisper model is already loaded and available as `model`.
    - The audio file should be in a format supported by the Whisper model (e.g., MP3, WAV).
    """

    logger.info("Generating timestamps...")

    wordTimestamps = []
    result = model.transcribe(audio, word_timestamps=True)

    for segment in result["segments"]:
        for word_info in segment["words"]:
            word = word_info["word"]
            start_time = word_info["start"]
            end_time = word_info["end"]
            wordTimestamps.append((word, float(start_time), float(end_time)))
    return wordTimestamps



def generate_srt(timestamps, output_path):
    logger.info("Generating SRT file...")

    with open(output_path, "w", encoding="utf-8") as srt_file:
        for i, (text, start, end) in enumerate(timestamps):
            srt_file.write(f"{i + 1}\n")
            srt_file.write(f"{format_time(start)} --> {format_time(end)}\n")
            srt_file.write(f"{text}\n\n")

    
    return output_path

def format_time(seconds):
    """
    Formats seconds into SRT timestamp format (HH:MM:SS,ms).
    """
    milliseconds = int((seconds % 1) * 1000)
    seconds = int(seconds)
    minutes, seconds = divmod(seconds, 60)
    hours, minutes = divmod(minutes, 60)
    return f"{hours:02}:{minutes:02}:{seconds:02},{milliseconds:03}"


async def add_subtitles():
    logger.info("Running FFMPEG command...")

    command = [
        "ffmpeg",
        "-i", "output_video.mp4",
        "-vf", f"subtitles=output_captions.srt",
        "-c:a", "copy",
        "generated.mp4"
    ]
    await asyncio.to_thread(subprocess.run, command, check=True)


from fastapi import FastAPI, File, UploadFile, Form, BackgroundTasks
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
import uuid

app = FastAPI()
logger = logging.getLogger('uvicorn.error')
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
async def subtitleEndpoint(background_tasks: BackgroundTasks, file: UploadFile=File(...), font: str=Form(...)):
    logger.info('generating subtitles...')

    file_uuid = uuid.uuid4()
    video_path = "video-" + str(file_uuid) + ".mp4"
    srt_path = "subtitles-" + str(file_uuid) + ".srt"
    output_path = "generated-file" + "-" + str(file_uuid) + "-" + file.filename

    logger.info(video_path)
    logger.info(srt_path)
    logger.info(output_path)

    #process input file into numpy array to be used by whisper model
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
    generate_srt(word_timestamps, srt_path)

    #save the uploaded mp4 to disk
    save_upload_file(file, video_path)

    #run the ffmpeg command on the uploaded mp4 file with the srt file
    await add_subtitles(srt_path, video_path, output_path)

    def file_streamer(file_path):
        with open(file_path, "rb") as file:
            yield from file

    response = StreamingResponse(file_streamer(output_path), media_type="video/mp4")
    
    background_tasks.add_task(cleanup_files, video_path, srt_path, output_path)
    
    return response

def cleanup_files(*file_paths):
    """Deletes all temporary files after response is sent."""
    for file_path in file_paths:
        if os.path.exists(file_path):
            os.remove(file_path)
            logger.info(f"Deleted {file_path}")
        else:
            logger.warning(f"File not found for deletion: {file_path}")
    

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


async def add_subtitles(srt_path, video_path, output_path):
    logger.info("Running FFMPEG command...")

    command = [
        "ffmpeg",
        "-i", video_path,
        "-vf", f"subtitles={srt_path}",
        "-c:a", "copy",
        output_path
    ]
    await asyncio.to_thread(subprocess.run, command, check=True)
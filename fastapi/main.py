from fastapi import FastAPI, File, UploadFile, Form
from fastapi.responses import StreamingResponse
import subprocess
from io import BytesIO
from fastapi.middleware.cors import CORSMiddleware
import whisper
from pydub import AudioSegment
import numpy as np
import io
import tempfile
import shutil
import os
from pathlib import Path
from fastapi.responses import FileResponse

app = FastAPI()

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


    #process input file
    file_content = await file.read()
    audio = AudioSegment.from_file(BytesIO(file_content))
    if audio.channels > 1:
        audio = audio.set_channels(1)
    audio = audio.set_frame_rate(16000)
    samples = np.array(audio.get_array_of_samples(), dtype=np.float32)
    samples /= np.max(np.abs(samples))
    
    #input_file = BytesIO(file_content)
    """ return StreamingResponse(input_file, 
                             media_type=file.content_type,
                             headers={"Content-Disposition": f"attachment; filename={file.filename}"}
                            ) """

    wordTimestamps = speechToText(samples)
    #srt_file = generate_srt(wordTimestamps)

    #return True

    return add_subtitles(file, wordTimestamps)

    #convert word timestamps to an SRT File

    #generate new file with input mp4 and srt file

    #return resulting file


   
    


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

    wordTimestamps = []
    result = model.transcribe(audio, word_timestamps=True)

    for segment in result["segments"]:
        for word_info in segment["words"]:
            word = word_info["word"]
            start_time = word_info["start"]
            end_time = word_info["end"]
            wordTimestamps.append((word, float(start_time), float(end_time)))
    return wordTimestamps



def generate_srt(timestamps):

    #process srt content as a string and use a temp file with ffmpeg
    srt_file = io.StringIO()
    # Write to SRT file
    #with open("output_captions.srt", "w") as srt_file:
    for i in range(len(timestamps)):
        srt_file.write(f"{i + 1}\n")
        srt_file.write(f"{format_time(timestamps[i][1])} --> {format_time(timestamps[i][2])}\n")
        srt_file.write(f"{timestamps[i][0]}\n\n")
    
    return srt_file.getvalue()

def format_time(seconds):
    """
    Formats seconds into SRT timestamp format (HH:MM:SS,ms).
    """
    milliseconds = int((seconds % 1) * 1000)
    seconds = int(seconds)
    minutes, seconds = divmod(seconds, 60)
    hours, minutes = divmod(minutes, 60)
    return f"{hours:02}:{minutes:02}:{seconds:02},{milliseconds:03}"

def add_subtitles(video: UploadFile, timestamps):
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_dir = Path(temp_dir)
        video_path = temp_dir / video.filename
        subtitles_path = temp_dir / "output_captions.srt"
        output_path = temp_dir / f"subtitled_{video.filename}"

        # Save uploaded video file (ensure full read before writing)
        video_content = video.file.read()
        video.file.close()  # Explicitly close file handle
        with video_path.open("wb") as f:
            f.write(video_content)
            f.flush()
        print(f"Saved video file at: {video_path}, Size: {video_path.stat().st_size} bytes")

        # Generate SRT content
        srt_content = generate_srt(timestamps)
        with subtitles_path.open("w", encoding="utf-8") as f:
            f.write(srt_content)
        
        print(f"Saved subtitles file at: {subtitles_path}, Size: {subtitles_path.stat().st_size} bytes")

        # Run ffmpeg command to burn subtitles into video
        command = [
            "ffmpeg", "-y", "-analyzeduration", "100M", "-probesize", "100M",
            "-i", str(video_path), "-vf", f"subtitles={subtitles_path}", "-c:a", "copy", str(output_path)
        ]

        probe_command = ["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries", "format=duration", "-of", "json", str(video_path)]
        probe_result = subprocess.run(probe_command, capture_output=True, text=True)

        if probe_result.returncode != 0:
            raise RuntimeError(f"Invalid video file: {probe_result.stderr}")

        result = subprocess.run(command, capture_output=True, text=True)
        
        print("FFmpeg stdout:", result.stdout)
        print("FFmpeg stderr:", result.stderr)

        if result.returncode != 0:
            raise RuntimeError(f"FFmpeg error: {result.stderr}")

        return FileResponse(output_path, filename=output_path.name)


'''def add_subtitles(video_file: bytes, srt_content: str):
   

   #define subtitle style
   style = (
        "force_style='Fontname=Comic Sans MS,"
        "Fontsize=14,"
        "Bold=1,"
        "Alignment=6'"
    )

   #create temp srt file
   temp_srt = tempfile.NamedTemporaryFile(delete=False, suffix=".srt", mode="w", encoding="utf-8")
   temp_srt.write(srt_content)
   temp_srt.close()


   #create temp mp4 file from file content()
   temp_mp4 = tempfile.NamedTemporaryFile(delete=False, suffix=".mp4")
   temp_mp4.write(video_file)
   temp_mp4.close()

   temp_output = tempfile.NamedTemporaryFile(delete=False, suffix=".mp4")
   temp_output.close() 
   print(temp_srt.name)
   print(temp_mp4.name)

   srt_path = os.path.abspath(temp_srt.name).replace("\\", "/")  # Ensure absolute and properly formatted path
   mp4_path = os.path.abspath(temp_mp4.name).replace("\\", "/")
   output_path = os.path.abspath(temp_output.name).replace("\\", "/")

   print(f"FFmpeg paths:\nSRT: {srt_path}\nMP4: {mp4_path}\nOutput: {output_path}")

   command = [
        "ffmpeg",
        "-i", mp4_path,
        "-vf", f"subtitles={srt_path}",
        "-c:a", "copy",
        output_path
    ]
   
   #check mp4 and srt exist
   print(f"Checking SRT file existence: {os.path.exists(srt_path)}, path: {srt_path}")
   print(f"Checking MP4 file existence: {os.path.exists(mp4_path)}, path: {mp4_path}")

   
   result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
   print("FFmpeg stdout:", result.stdout)
   print("FFmpeg stderr:", result.stderr)
   if result.returncode != 0:
        raise Exception(f"FFmpeg failed: {result.stderr}")
   

   def iterfile():
        with open(temp_output.name, "rb") as file:
            yield from file
        # Cleanup files after streaming
        cleanup_temp_files([mp4_path, srt_path, output_path])
    

   return StreamingResponse(
        iterfile(),
        media_type="video/mp4",
        headers={"Content-Disposition": "attachment; filename=output.mp4"}
    )'''
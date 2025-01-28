from fastapi import FastAPI, File, UploadFile, Form
from fastapi.responses import StreamingResponse
import subprocess
from io import BytesIO
from fastapi.middleware.cors import CORSMiddleware
import whisper
from pydub import AudioSegment
import numpy as np

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
    
    

    wordTimestamps = speechToText(samples)

    #convert word timestamps to an SRT File

    #generate new file with input mp4 and srt file

    #return resulting file


    input_file = BytesIO(file_content)
    return StreamingResponse(input_file, 
                             media_type=file.content_type,
                             headers={"Content-Disposition": f"attachment; filename={file.filename}"}
                            )
    


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
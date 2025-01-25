from fastapi import FastAPI, File, UploadFile, Form
from fastapi.responses import StreamingResponse
import subprocess
from io import BytesIO
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

# Allow CORS from specific origins (like your React app's port)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # React app's address
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods (GET, POST, etc.)
    allow_headers=["*"],  # Allows all headers
)

@app.post("/generate-subtitles")
async def root( file: UploadFile=File(...), font: str=Form(...)):

    file_content = await file.read()
    input_file = BytesIO(file_content)
    print(file.filename)
    return StreamingResponse(input_file, 
                             media_type=file.content_type,
                             headers={"Content-Disposition": f"attachment; filename={file.filename}"}
                            )
    



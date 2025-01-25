from fastapi import FastAPI, File, UploadFile, Form
from fastapi.responses import StreamingResponse
import subprocess
from io import BytesIO

app = FastAPI()

@app.post("/generate-subtitles")
async def root( file: UploadFile=File(...), font: str=Form(...)):

    file_content = await file.read()
    input_file = BytesIO(file_content)
    print(file.content_type)
    return StreamingResponse(input_file, 
                             media_type=file.content_type,
                             headers={"Content-Disposition": f"attachment; filename={file.filename}"}
                            )
    



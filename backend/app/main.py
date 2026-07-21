from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from .colorimetry import analyze_strip

app = FastAPI(
    title="Urine Test Strip Colorimetry API",
    description="Point-of-care colorimetric analysis of urine test strips",
    version="1.0.0",
)

# Allow the React dev server (and deployed frontend) to call this API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],   # restrict to your frontend URL in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def root():
    return {"message": "Urine Strip Colorimetry API is running"}


@app.post("/analyze")
async def analyze(file: UploadFile = File(...)):
    if not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="File must be an image")

    image_bytes = await file.read()

    try:
        results = analyze_strip(image_bytes)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    return {
        "filename": file.filename,
        "results": results
    }
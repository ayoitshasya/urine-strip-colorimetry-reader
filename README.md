# 🧪 Urine Test Strip Reader using Colorimetry

A point-of-care web application that analyzes photos of urine test strips and estimates diagnostic parameters (Glucose, Protein, pH, Ketones, Blood) using colorimetric image analysis — removing the subjectivity of manual visual chart-matching.

---

## 📖 Overview

Urine test strips contain reagent pads that change color when exposed to specific substances in urine. Traditionally, results are read by visually comparing pad colors against a printed reference chart — a method prone to human error from inconsistent lighting, color perception, and judgment.

This project automates that process using **colorimetry**: the science of measuring color to determine chemical concentrations. The system extracts the actual RGB pixel values from an uploaded strip image and mathematically matches them against a digital reference chart to return an objective, repeatable result.

---

## 🛠️ Tech Stack

| Layer | Technology | Reason |
|---|---|---|
| Frontend | React (Vite) + React Router | Component-based UI, fast dev server, easy multi-page routing |
| Backend | FastAPI (Python) | Lightweight, async, auto-generated API docs |
| Image Processing | OpenCV, NumPy, Pillow | Industry-standard tools for pixel/color analysis |
| HTTP Client | Axios | Simple promise-based API calls from frontend |
| Hosting (Frontend) | Vercel | Free, optimized for React/Vite deployments |
| Hosting (Backend) | Render | Free tier supports persistent Python web services |

---

## 📁 Project Structure

```
urine-strip-reader/
├── backend/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py              # FastAPI app + /analyze endpoint
│   │   ├── colorimetry.py       # Image decoding + color extraction + matching logic
│   │   ├── reference_data.py    # Reference color chart + pad position data
│   │   └── schemas.py           # Pydantic response models
│   └── requirements.txt
│
├── frontend/
│   ├── src/
│   │   ├── api/
│   │   │   └── api.js           # Axios call to backend /analyze endpoint
│   │   ├── components/
│   │   │   ├── Navbar.jsx
│   │   │   ├── UploadForm.jsx
│   │   │   └── ResultsDisplay.jsx
│   │   ├── pages/
│   │   │   ├── Home.jsx
│   │   │   ├── Analyze.jsx
│   │   │   ├── About.jsx
│   │   │   └── Contact.jsx
│   │   ├── App.jsx
│   │   ├── App.css
│   │   ├── main.jsx
│   │   └── index.css
│   ├── index.html
│   └── package.json
│
├── .gitignore
└── README.md
```

---

## ⚙️ How It Works

1. **User uploads** a photo of a urine test strip via the React frontend (`/analyze` page).
2. The image is sent as `multipart/form-data` to the FastAPI backend's `POST /analyze` endpoint.
3. **OpenCV** decodes the image into a pixel array.
4. For each parameter (Glucose, Protein, pH, Ketones, Blood), the backend samples a small patch of pixels at the pad's expected horizontal position on the strip and computes the **average RGB color**.
5. Each detected color is compared against a **reference color chart** (`reference_data.py`) using **Euclidean distance** — the closest matching reference color determines the result level (e.g., Negative, Trace, +1, +2, +3).
6. The backend returns a JSON response with detected colors and matched results.
7. The React frontend displays each parameter as a card with a color swatch and the interpreted result.

### Data Flow Diagram
```
[User uploads image] 
        ↓
[React sends POST /analyze request] 
        ↓
[FastAPI receives image bytes]
        ↓
[OpenCV extracts pad colors]
        ↓
[Colors matched against reference chart]
        ↓
[JSON results returned]
        ↓
[React renders results + color swatches]
```

---

## 🚀 Getting Started (Local Setup)

### Prerequisites
- Python 3.9+
- Node.js 18+ and npm
- Git

### Backend Setup
```bash
cd backend
python -m venv venv

# Activate virtual environment
source venv/bin/activate        # Mac/Linux
venv\Scripts\activate           # Windows

pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```
Backend runs at: `http://localhost:8000`  
API docs available at: `http://localhost:8000/docs`

### Frontend Setup
```bash
cd frontend
npm install
npm run dev
```
Frontend runs at: `http://localhost:5173`

---

## 🔌 API Reference

### `GET /`
Health check endpoint.

**Response:**
```json
{ "message": "Urine Strip Colorimetry API is running" }
```

### `POST /analyze`
Analyzes an uploaded strip image.

**Request:** `multipart/form-data` with a `file` field (image)

**Response:**
```json
{
  "filename": "test_strip.png",
  "results": {
    "Glucose": {
      "detected_rgb": [120, 170, 70],
      "result": "+1",
      "matched_reference_rgb": [120, 170, 70],
      "distance": 0.0
    },
    "Protein": { ... },
    "pH": { ... },
    "Ketones": { ... },
    "Blood": { ... }
  }
}
```

---

## 🌐 Deployment

| Component | Platform | Notes |
|---|---|---|
| Backend | [Render](https://render.com) | Free tier; root directory: `backend`; start command: `uvicorn app.main:app --host 0.0.0.0 --port $PORT` |
| Frontend | [Vercel](https://vercel.com) | Free tier; root directory: `frontend`; auto-deploys on push to `main` |

> Note: Free-tier Render services sleep after inactivity and may take 30–50 seconds to wake up on first request.

---

## ⚠️ Limitations & Calibration Note

The reference colors and pad positions in `reference_data.py` are **approximate placeholder values**. For real-world accuracy, they should be recalibrated using:
- An actual photograph of the specific test strip brand's printed reference chart, under consistent lighting
- Precise pad position measurements for that brand's strip layout

This project is intended as an educational/proof-of-concept demonstration of colorimetric analysis, not a clinically validated diagnostic tool.

---

## 👤 Author

**Project:** KJS-HC-03-1 — Urine Test Strip Reader using Colorimetry as a Point-of-Care Technology  
**Institution:** K J Somaiya School of Engineering  
**Course:** Digital Marketing (DiM) — Sem VII


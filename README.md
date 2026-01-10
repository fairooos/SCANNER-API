# SCANNER - Document OCR System

Production-grade document scanning system for Emirates ID and Passport processing.

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                         Frontend                            │
│                    (HTML + Vanilla JS)                      │
└──────────────────────┬──────────────────────────────────────┘
                       │ HTTP/REST
                       ▼
┌─────────────────────────────────────────────────────────────┐
│                       FastAPI Backend                        │
│  ┌──────────────────────────────────────────────────────┐   │
│  │               API Layer (v1)                         │   │
│  │  - /api/v1/health                                    │   │
│  │  - /api/v1/id/scan                                   │   │
│  │  - /api/v1/passport/scan                             │   │
│  └────────┬─────────────────────┬────────────────────────┘   │
│           │                     │                            │
│  ┌────────▼─────────┐  ┌────────▼─────────┐                 │
│  │ Emirates ID      │  │ Passport         │                 │
│  │ Pipeline         │  │ Pipeline         │                 │
│  │                  │  │                  │                 │
│  │ YOLO Detection   │  │ Passporteye      │                 │
│  │ + EasyOCR        │  │ (MRZ Parser)     │                 │
│  └──────────────────┘  └──────────────────┘                 │
│                                                              │
│  ┌──────────────────────────────────────────────────────┐   │
│  │            Utilities & Validators                    │   │
│  │  - Text normalization                                │   │
│  │  - Field validation                                  │   │
│  │  - Image preprocessing                               │   │
│  └──────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
```

## Features

### Emirates ID Processing
- YOLO-based field detection (7 fields)
- EasyOCR text extraction
- Automatic text normalization
- Emirates ID number validation
- Date consistency validation
- Per-field confidence scores

### Passport Processing
- MRZ (Machine Readable Zone) extraction
- ICAO 9303 compliance
- Checksum validation
- Automatic date parsing
- Nationality normalization

### API Features
- OpenAPI/Swagger documentation at `/docs`
- ReDoc documentation at `/redoc`
- CORS enabled for frontend
- Structured error responses
- Processing time tracking
- Non-critical warnings system

## Installation

### Prerequisites
- Python 3.9+
- YOLO model file (`best.pt`)
- GPU (optional, recommended for faster processing)

### Backend Setup

1. **Navigate to backend directory**:
   ```bash
   cd backend
   ```

2. **Create virtual environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Place YOLO model**:
   ```bash
   # Copy your best.pt file to backend/models/
   mkdir -p models
   cp /path/to/your/best.pt models/best.pt
   ```

5. **Run the server**:
   ```bash
   python run.py
   ```

   The API will start at `http://localhost:8000`

### Frontend Setup

1. **Open frontend**:
   ```bash
   # Simply open frontend/index.html in a browser
   # Or serve with a simple HTTP server:
   cd frontend
   python -m http.server 3000
   ```

2. **Access the UI**:
   - Open `http://localhost:3000` in your browser

## API Documentation

### Interactive Swagger UI
Navigate to `http://localhost:8000/docs` for interactive API documentation.

### Endpoints

#### Health Check
```http
GET /api/v1/health
```

**Response**:
```json
{
  "status": "healthy",
  "timestamp": "2026-01-10T12:00:00",
  "version": "1.0.0"
}
```

#### Scan Emirates ID
```http
POST /api/v1/id/scan
Content-Type: multipart/form-data

file: <image_file>
```

**Response**:
```json
{
  "document_type": "emirates_id",
  "fields": {
    "id_number": {
      "value": "784-2020-1234567-1",
      "confidence": 0.95,
      "bbox": [100, 200, 300, 250]
    },
    "full_name": {
      "value": "Ahmed Ali Mohammed",
      "confidence": 0.92,
      "bbox": [100, 260, 400, 310]
    }
    // ... other fields
  },
  "processing_time_ms": 1234.56,
  "warnings": [],
  "metadata": {
    "model": "YOLO + EasyOCR"
  }
}
```

#### Scan Passport
```http
POST /api/v1/passport/scan
Content-Type: multipart/form-data

file: <image_file>
```

**Response**:
```json
{
  "document_type": "passport",
  "fields": {
    "full_name": {
      "value": "Ahmed Ali Mohammed",
      "confidence": 0.95
    },
    "passport_number": {
      "value": "A12345678",
      "confidence": 0.95
    }
    // ... other fields
  },
  "processing_time_ms": 890.12,
  "warnings": [],
  "metadata": {
    "model": "passporteye (MRZ)",
    "standard": "ICAO 9303"
  }
}
```

## Configuration

Edit `backend/app/core/config.py` to customize:

- **File upload limits**: `MAX_FILE_SIZE_MB`
- **Confidence thresholds**: `MIN_DETECTION_CONFIDENCE`, `MIN_OCR_CONFIDENCE`
- **Model paths**: `YOLO_MODEL_PATH`
- **EasyOCR settings**: `EASYOCR_LANGUAGES`, `EASYOCR_GPU`
- **Date formats**: `DATE_INPUT_FORMATS`, `DATE_OUTPUT_FORMAT`

## Testing

### Using cURL

**Emirates ID**:
```bash
curl -X POST "http://localhost:8000/api/v1/id/scan" \
  -H "accept: application/json" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@/path/to/emirates_id.jpg"
```

**Passport**:
```bash
curl -X POST "http://localhost:8000/api/v1/passport/scan" \
  -H "accept: application/json" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@/path/to/passport.jpg"
```

### Using Frontend
1. Open `http://localhost:3000`
2. Select document type (Emirates ID or Passport)
3. Upload image via click or drag-drop
4. Click scan button
5. View extracted results

## Project Structure Explained

```
scanner/
├── backend/
│   ├── app/
│   │   ├── api/v1/          # API endpoints (clean REST architecture)
│   │   ├── core/            # Configuration & exceptions
│   │   ├── models/          # Pydantic request/response models
│   │   ├── pipelines/       # Document processing pipelines
│   │   │   ├── base.py      # Abstract base pipeline
│   │   │   ├── emirates_id.py  # Emirates ID pipeline
│   │   │   └── passport.py     # Passport pipeline
│   │   └── utils/           # Shared utilities
│   ├── models/              # ML models (YOLO best.pt)
│   └── requirements.txt
└── frontend/
    └── index.html           # Single-page UI
```

## Key Design Decisions

### 1. **Pipeline Separation**
Emirates ID and Passport pipelines are **completely separate classes** inheriting from `BasePipeline`. This ensures:
- Clean separation of concerns
- Easy to add new document types
- No logic leakage between document types

### 2. **Stateless Architecture**
- No database or persistence
- Each request is independent
- Models loaded once at startup (singleton pattern)

### 3. **Error Handling**
- Custom exception hierarchy (`ScannerBaseException`)
- Structured error responses (no stack traces exposed)
- Non-blocking warnings for validation issues

### 4. **Confidence Tracking**
- Both detection and OCR confidence tracked
- Combined using geometric mean to penalize weak links
- Per-field confidence in responses

### 5. **Normalization Pipeline**
- Separate normalization functions per field type
- Handles common OCR errors (O→0, I→1, etc.)
- Date format standardization

## Troubleshooting

### Model not found error
```
Ensure best.pt is placed in backend/models/best.pt
```

### CUDA/GPU errors
```python
# Edit backend/app/core/config.py
EASYOCR_GPU: bool = False  # Disable GPU
```

### CORS errors in frontend
```
Ensure API is running on localhost:8000
Check ALLOWED_ORIGINS in config.py
```

### Low confidence results
```
- Ensure image is clear and well-lit
- Check image is properly oriented
- Verify all text is visible and in focus
```

## Production Deployment

### Recommendations
1. **Use Gunicorn/Uvicorn workers**:
   ```bash
   gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker
   ```

2. **Add proper logging**:
   - Integrate with CloudWatch, Datadog, etc.
   - Log all requests and errors

3. **Restrict CORS**:
   - Update `ALLOWED_ORIGINS` in config

4. **Add authentication**:
   - Use FastAPI dependencies for API keys/JWT

5. **Add rate limiting**:
   - Use libraries like `slowapi`

6. **Monitor performance**:
   - Track processing times
   - Set up alerts for slow requests

7. **Scale horizontally**:
   - Run multiple instances behind load balancer
   - Share model files via shared storage

## License

Internal use only.

## Support

For issues or questions, contact the engineering team.
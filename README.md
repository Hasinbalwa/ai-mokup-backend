# AI Mockup Backend (Demo)

This simple Flask backend overlays an uploaded logo on a sample product image and returns a PNG mockup.

## Quick overview
- Endpoint: `POST /generate-mockup`
  - form-data fields:
    - `product` - product key (e.g. `cup`, `box`, `bag`)
    - `logo` - image file upload (png/jpg)
  - Returns: PNG image with logo overlayed.

- Endpoint: `GET /products` returns available product keys.

## Local run (recommended for testing)
1. Create virtual env and install:
```bash
python -m venv venv
# Windows
venv\\Scripts\\activate
# mac/linux
source venv/bin/activate
pip install -r requirements.txt
```

2. Run locally:
```bash
python app.py
# or
gunicorn app:app
```

3. Test with curl (example):
```bash
curl -X POST "http://127.0.0.1:5000/generate-mockup" -F "product=cup" -F "logo=@/path/to/your/logo.png" --output mockup.png
```

## Deploy
Push this repo to GitHub, then deploy to Render/Heroku. Use `gunicorn app:app` as start command.

---
This repository includes 3 sample placeholder product images in `static/products/` so you can test immediately.

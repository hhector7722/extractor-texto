# Extraer texto de imagen (OCR)

Aplicación para extraer texto de imágenes: arrastra una imagen, pégala con Ctrl+V o haz clic para seleccionar. Usa Tesseract OCR (español e inglés).

## Estructura

- **frontend/** — Interfaz React + Vite (subida a Vercel)
- **api.py** — API FastAPI con OCR (desplegar en Railway, Render o Fly.io)
- **ocr_app.py** — Versión escritorio con Tkinter (Ctrl+V desde portapapeles)

## Cómo ejecutarlo en local

1. **Tesseract:** instala [Tesseract OCR](https://github.com/tesseract-ocr/tesseract) y, en Windows, ajusta la ruta en `api.py` y `ocr_app.py` si hace falta.

2. **Backend:**
   ```bash
   pip install -r requirements.txt
   uvicorn api:app --reload --port 8000
   ```

3. **Frontend:**
   ```bash
   cd frontend && npm install && npm run dev
   ```

4. Abre http://localhost:5173 y sube o pega una imagen.

## Despliegue en producción

- **Frontend:** Vercel (ver `vercel.json`). Variable de entorno: `VITE_API_URL` con la URL de tu API.
- **API:** Railway, Render o Fly.io con Docker + Tesseract. Ver **DEPLOY.md**.

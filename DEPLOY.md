# Despliegue en producción

## Sí, puedes subirla a Vercel

El **frontend** (la interfaz) está preparado para desplegarse en **Vercel**. La **API** (Python + Tesseract) no puede ejecutarse en Vercel y debe alojarse en otro servicio.

---

## 1. Desplegar el frontend en Vercel

1. Sube el proyecto a **GitHub** (si aún no lo has hecho).
2. Entra en [vercel.com](https://vercel.com) e importa el repositorio.
3. **No cambies** el directorio raíz: el `vercel.json` en la raíz ya indica cómo construir el frontend.
4. En **Environment Variables** añade (solo cuando tengas la API en producción):
   - **Name:** `VITE_API_URL`  
   - **Value:** `https://tu-api-en-railway-o-render.com` (URL de tu API, **sin** barra final)
5. Despliega. Vercel hará `npm install` y `npm run build` dentro de `frontend` y servirá `frontend/dist`.

Tu app estará en una URL tipo `https://tu-proyecto.vercel.app`.

---

## 2. Dónde desplegar la API (Python + Tesseract)

En Vercel no se puede usar Tesseract (binarios nativos). Tienes que alojar la API en un servicio que permita Python y dependencias nativas, por ejemplo:

| Servicio   | Ventaja                          | Cómo usar Tesseract                    |
|-----------|-----------------------------------|----------------------------------------|
| **Railway** | Muy sencillo, soporta Docker      | Usar imagen con Tesseract instalado    |
| **Render**  | Plan gratuito, soporta Docker     | Igual: imagen con Tesseract            |
| **Fly.io**  | Buena opción para APIs globales   | Dockerfile con Tesseract                |

Ejemplo mínimo de **Dockerfile** para la API (en la raíz del repo, junto a `api.py`):

```dockerfile
FROM python:3.11-slim

RUN apt-get update && apt-get install -y tesseract-ocr tesseract-ocr-spa && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY api.py .

EXPOSE 8000
CMD ["uvicorn", "api:app", "--host", "0.0.0.0", "--port", "8000"]
```

En Railway/Render/Fly subes este Dockerfile y el `api.py`; te darán una URL (ej. `https://tu-api.railway.app`). Esa URL es la que pones en **VITE_API_URL** en Vercel.

---

## 3. Resumen

- **Frontend** → Vercel (ya configurado con `vercel.json`).
- **API** → Railway, Render o Fly.io con Docker + Tesseract.
- En Vercel: variable de entorno **VITE_API_URL** = URL pública de tu API (sin barra final).

Si despliegas solo el frontend en Vercel y **no** configuras `VITE_API_URL`, la app cargará pero al subir una imagen fallará hasta que la API esté desplegada y la variable configurada.

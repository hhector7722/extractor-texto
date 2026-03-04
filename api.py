import io
import re
import os
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from PIL import Image, ImageOps, ImageFilter, ImageStat
import pytesseract

# ==========================================
# CONFIGURATION
# ==========================================
# If Tesseract is not in your PATH, set the path below:
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

app = FastAPI(title="Antigravity OCR API")

# Setup CORS for local React development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class OCRProcessor:
    @staticmethod
    def preprocess_image(image: Image.Image) -> Image.Image:
        # Convert to grayscale
        if image.mode != 'L':
            image = ImageOps.grayscale(image)
        
        # 1. Upsample 2x
        w, h = image.size
        image = image.resize((w * 2, h * 2), Image.Resampling.LANCZOS)
        
        # 2. Check for Dark Mode and Invert
        stat = ImageStat.Stat(image)
        if stat.mean[0] < 127:
            image = ImageOps.invert(image)
            
        # 3. Increase contrast and apply threshold
        threshold = 150
        image = image.point(lambda p: 255 if p > threshold else 0)
        
        # Optional: sharpen
        image = image.filter(ImageFilter.SHARPEN)
        
        return image

    @staticmethod
    def extract_text(image: Image.Image) -> str:
        try:
            custom_config = r'--oem 3 --psm 6'
            text = pytesseract.image_to_string(image, lang='eng+spa', config=custom_config)
            
            cleaned_lines = []
            for line in text.split('\n'):
                line = re.sub(r'[^\w\s]', ' ', line)
                line = re.sub(r'\s+', ' ', line).strip()
                if line and any(c.isalnum() for c in line):
                    cleaned_lines.append(line)
                
            return "\n".join(cleaned_lines).strip()
        except Exception as e:
            raise RuntimeError(f"Error procesando OCR: {str(e)}")

@app.post("/api/extract")
async def extract_text(file: UploadFile = File(...)):
    if not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="El archivo no es una imagen válida.")
    
    try:
        content = await file.read()
        image = Image.open(io.BytesIO(content))
        
        # Process
        processor = OCRProcessor()
        processed_img = processor.preprocess_image(image)
        text = processor.extract_text(processed_img)
        
        return {"text": text}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
def health_check():
    return {"status": "ok"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

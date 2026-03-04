import tkinter as tk
from tkinter import messagebox, scrolledtext
import threading
from typing import Optional
from PIL import Image, ImageGrab, ImageOps, ImageFilter, ImageStat
import pytesseract
import pyperclip
import os
import sys
import re

# ==========================================
# CONFIGURATION
# ==========================================
# If Tesseract is not in your PATH, uncomment and set the path below:
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

class OCRProcessor:
    """Handles image pre-processing and OCR extraction."""
    
    @staticmethod
    def preprocess_image(image: Image.Image) -> Image.Image:
        """
        Enhances image for better OCR results:
        1. Rescale (Upsample) - Essential for low DPI screenshots.
        2. Automatic Inversion - Tesseract prefers black text on white background.
        3. Thresholding (Binarization).
        """
        # Convert to grayscale
        image = ImageOps.grayscale(image)
        
        # 1. Upsample 2x (LANCZOS for quality)
        w, h = image.size
        image = image.resize((w * 2, h * 2), Image.Resampling.LANCZOS)
        
        # 2. Check for Dark Mode and Invert
        # If the average pixel is dark (< 127), we invert so it's dark text on light base.
        stat = ImageStat.Stat(image)
        if stat.mean[0] < 127:
            image = ImageOps.invert(image)
            
        # 3. Increase contrast and apply threshold
        # Now that we have light background, we push it to pure white.
        threshold = 150
        image = image.point(lambda p: 255 if p > threshold else 0)
        
        # Optional: sharpen after thresholding to define edges
        image = image.filter(ImageFilter.SHARPEN)
        
        return image

    @staticmethod
    def extract_text(image: Image.Image) -> str:
        """Runs Tesseract OCR with optimized config and cleans symbols."""
        try:
            # Config: --psm 6 assumes a single uniform block of text
            custom_config = r'--oem 3 --psm 6'
            text = pytesseract.image_to_string(image, lang='eng+spa', config=custom_config)
            
            # Post-processing: Replace symbols with spaces and clean up
            cleaned_lines = []
            for line in text.split('\n'):
                # 1. Replace all non-alphanumeric (including Spanish characters) with a space
                # [^\w\s] is too broad because \w in Python 3 includes Unicode characters (accents, ñ).
                # We target anything that IS NOT: letter, digit, or whitespace.
                # Then we replace it with a space.
                line = re.sub(r'[^\w\s]', ' ', line)
                
                # 2. Collapse multiple spaces into one
                line = re.sub(r'\s+', ' ', line).strip()
                
                if not line:
                    continue
                
                # 3. Only keep lines that have actual alphanumeric content 
                # (prevents lines that were just symbols from becoming empty noise)
                if any(c.isalnum() for c in line):
                    cleaned_lines.append(line)
                
            return "\n".join(cleaned_lines).strip()
        except pytesseract.TesseractNotFoundError:
            raise EnvironmentError(
                "Tesseract-OCR no encontrado.\n\n"
                "Asegúrate de tenerlo instalado y añadido al PATH, "
                "o configura 'tesseract_cmd' en el script."
            )
        except Exception as e:
            raise RuntimeError(f"Error procesando OCR: {str(e)}")

class OCRApp:
    """Main GUI Application."""
    
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("Antigravity OCR - Clipboard tool")
        self.root.geometry("600x450")
        self.root.configure(bg="#2d2d2d")
        
        self.processor = OCRProcessor()
        self.setup_ui()
        self.setup_bindings()

    def setup_ui(self):
        """Initializes the UI components."""
        # Header Label
        header = tk.Label(
            self.root, 
            text="Pega una imagen (Ctrl + V) para extraer texto",
            font=("Segoe UI", 12, "bold"),
            bg="#2d2d2d",
            fg="#ffffff",
            pady=10
        )
        header.pack(fill=tk.X)

        # Text Area
        self.text_area = scrolledtext.ScrolledText(
            self.root,
            wrap=tk.WORD,
            font=("Consolas", 11),
            bg="#1e1e1e",
            fg="#d4d4d4",
            insertbackground="white",
            padx=10,
            pady=10
        )
        self.text_area.pack(expand=True, fill=tk.BOTH, padx=15, pady=5)

        # Status Bar
        self.status_var = tk.StringVar(value="Listo.")
        self.status_bar = tk.Label(
            self.root,
            textvariable=self.status_var,
            bd=1,
            relief=tk.SUNKEN,
            anchor=tk.W,
            bg="#333333",
            fg="#aaaaaa",
            font=("Segoe UI", 9)
        )
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)

    def setup_bindings(self):
        """Binds events like Ctrl+V."""
        # Note: <Control-v> works for lowercase 'v' which is standard
        self.root.bind("<Control-v>", lambda e: self.handle_paste())
        self.root.bind("<Control-V>", lambda e: self.handle_paste())

    def update_status(self, message: str, color: str = "#aaaaaa"):
        """Safely updates status bar from any thread."""
        self.root.after(0, lambda: self._do_update_status(message, color))

    def _do_update_status(self, message: str, color: str):
        self.status_var.set(message)
        self.status_bar.config(fg=color)

    def set_loading(self, is_loading: bool):
        """Toggles 'disabled' state to prevent multiple concurrent runs."""
        if is_loading:
            self.update_status("Procesando OCR...", "#3498db")
            self.text_area.config(state=tk.DISABLED)
        else:
            self.text_area.config(state=tk.NORMAL)

    def handle_paste(self):
        """Entry point for Ctrl+V event."""
        # Trigger processing in a background thread to keep UI interactive
        threading.Thread(target=self.process_clipboard, daemon=True).start()

    def process_clipboard(self):
        """Logic for fetching clipboard data and OCR."""
        try:
            # Grab image from clipboard
            img = ImageGrab.grabclipboard()
            
            if img is None:
                # Removed popup and replaced with silent status message
                self.update_status("Portapapeles vacío o no contiene una imagen.", "#f1c40f")
                return

            # Ensure it's a PIL Image
            if not isinstance(img, Image.Image):
                self.update_status("Contenido no válido (no es una imagen).", "#e74c3c")
                return

            self.root.after(0, lambda: self.set_loading(True))

            # 1. Pre-process
            processed_img = self.processor.preprocess_image(img)
            
            # 2. OCR Extraction
            extracted_text = self.processor.extract_text(processed_img)

            # 3. Handle Results
            if extracted_text:
                pyperclip.copy(extracted_text)
                self.root.after(0, lambda: self.display_result(extracted_text))
                self.update_status("¡Texto extraído y copiado al portapapeles!", "#2ecc71")
            else:
                self.update_status("No se encontró texto en la imagen.", "#f1c40f")
            
        except EnvironmentError as ee:
            self.root.after(0, lambda: messagebox.showerror("Tesseract no configurado", str(ee)))
            self.update_status("Error: Tesseract no encontrado.", "#e74c3c")
        except Exception as e:
            self.root.after(0, lambda: messagebox.showerror("Error", f"Ocurrió un error inesperado:\n{str(e)}"))
            self.update_status("Error en el procesamiento.", "#e74c3c")
        finally:
            self.root.after(0, lambda: self.set_loading(False))

    def display_result(self, text: str):
        """Updates the text area with the result."""
        self.text_area.config(state=tk.NORMAL)
        self.text_area.delete(1.0, tk.END)
        self.text_area.insert(tk.END, text)

# ==========================================
# MAIN EXECUTION
# ==========================================
if __name__ == "__main__":
    # Check dependencies if running directly
    # Note: This script assumes pytesseract, Pillow, and pyperclip are installed via pip.
    
    root = tk.Tk()
    app = OCRApp(root)
    root.mainloop()

# TO INSTALL DEPENDENCIES:
# pip install pytesseract Pillow pyperclip

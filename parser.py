# parser.py
import os
import fitz
import pytesseract
from PIL import Image
from docx import Document


def clean(text: str) -> str:
    if not text:
        return ""
    return " ".join(text.split())


def read_pdf(path):
    text = ""

    try:
        doc = fitz.open(path)

        # try text layer first
        text = " ".join([page.get_text("text") for page in doc])

        # fallback OCR if empty
        if len(text.strip()) < 50:
            ocr_text = []
            for page in doc:
                pix = page.get_pixmap(dpi=200)
                img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
                ocr_text.append(pytesseract.image_to_string(img))
            text = " ".join(ocr_text)

    except Exception:
        return ""

    return clean(text)


def read_docx(path):
    try:
        doc = Document(path)
        return clean(" ".join([p.text for p in doc.paragraphs]))
    except:
        return ""


def read_image(path):
    try:
        return clean(pytesseract.image_to_string(Image.open(path)))
    except:
        return ""


def read_txt(path):
    try:
        with open(path, "r", encoding="utf-8", errors="ignore") as f:
            return clean(f.read())
    except:
        return ""


def read_file(path):
    """
    UNIVERSAL ATS FILE READER
    """
    if not os.path.exists(path):
        return ""

    ext = path.lower().split(".")[-1]

    if ext == "pdf":
        return read_pdf(path)
    elif ext == "docx":
        return read_docx(path)
    elif ext in ["png", "jpg", "jpeg"]:
        return read_image(path)
    else:
        return read_txt(path)
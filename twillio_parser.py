import os
import re
import requests
import spacy
import fitz  # PyMuPDF
import magic
import dateparser
import pytesseract
from docx import Document
from PIL import Image
from datetime import datetime
from sentence_transformers import SentenceTransformer, util
from fastapi import FastAPI, Form, Response
from twilio.twiml.messaging_response import MessagingResponse
from requests.auth import HTTPBasicAuth

# --- 1. THE CORE ENGINE ---

# Global models
nlp = spacy.load("en_core_web_md")
semantic_model = SentenceTransformer('all-MiniLM-L6-v2')

class EnterpriseATS:
    def __init__(self, jd_path):
        self.jd_text = self.universal_read(jd_path)
        self.jd_embedding = semantic_model.encode(self.jd_text)
        self.skills_taxonomy = ["Python", "Java", "SQL", "AWS", "Azure", "Docker", "Kubernetes", "React", "Project Management", "Agile"]

    def universal_read(self, path):
        mime = magic.Magic(mime=True)
        file_type = mime.from_file(path)

        if "image" in file_type or "webp" in file_type:
            return pytesseract.image_to_string(Image.open(path))
        
        if "officedocument" in file_type:
            doc = Document(path)
            return " ".join([p.text for p in doc.paragraphs])

        if "pdf" in file_type:
            with fitz.open(path) as doc:
                text = " ".join([page.get_text() for page in doc])
                if len(text.strip()) < 50: 
                    # Scanned PDF Fallback
                    full_text = []
                    for page in doc:
                        pix = page.get_pixmap()
                        img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
                        full_text.append(pytesseract.image_to_string(img))
                    return " ".join(full_text)
                return text
        return ""

    def extract_experience(self, text):
        date_patterns = re.findall(r'(\d{4}|[A-Z][a-z]+ \d{4}).*?(\d{4}|[A-Z][a-z]+ \d{4}|Present|Current)', text)
        total_months = 0
        for start, end in date_patterns:
            try:
                s_dt = dateparser.parse(start)
                e_dt = datetime.now() if end.lower() in ['present', 'current'] else dateparser.parse(end)
                if s_dt and e_dt:
                    total_months += (e_dt.year - s_dt.year) * 12 + (e_dt.month - s_dt.month)
            except: continue
        return round(total_months / 12, 1)

    def parse_resume(self, path):
        text = self.universal_read(path)
        doc = nlp(text)
        email = re.search(r'[\w\.-]+@[\w\.-]+', text)
        
        name = "Unknown Candidate"
        orgs = []
        for ent in doc.ents:
            if ent.label_ == "PERSON" and name == "Unknown Candidate": name = ent.text
            if ent.label_ == "ORG": orgs.append(ent.text)

        found_skills = [s for s in self.skills_taxonomy if s.lower() in text.lower()]
        res_embedding = semantic_model.encode(text)
        score = util.cos_sim(self.jd_embedding, res_embedding).item()

        return {
            "name": name,
            "email": email.group(0) if email else "N/A",
            "years_exp": self.extract_experience(text),
            "skills": list(set(found_skills)),
            "companies": list(set(orgs))[:3],
            "score": round(score * 100, 2)
        }

# --- 2. FASTAPI WEB SERVER ---

app = FastAPI()

# Configuration
JD_FILE = "/home/credentek/Downloads/software-engineer-job-description-template.pdf"
TWILIO_SID = os.getenv('AC6931b267a3687934c0b49f2b0a1b6e1a')
TWILIO_TOKEN = os.getenv('95f31fa011c9bfda56ca7b9fd47b032d')

# Initialize ATS
if not os.path.exists(JD_FILE):
    print(f"⚠️ Warning: JD file not found at {JD_FILE}. System may fail.")
ats = EnterpriseATS(JD_FILE)

@app.post("/whatsapp")
async def handle_whatsapp(
    MediaUrl0: str = Form(None), 
    MediaContentType0: str = Form(None),
    From: str = Form(...)
):
    twiml_resp = MessagingResponse()
    
    if not MediaUrl0:
        twiml_resp.message("👋 Hello! Please upload your resume (PDF or Image) here to apply.")
        return Response(content=str(twiml_resp), media_type="application/xml")

    # Determine Extension
    ext = ".pdf"
    if "officedocument" in str(MediaContentType0): ext = ".docx"
    elif "image" in str(MediaContentType0): ext = ".jpg"
    
    filename = f"temp_{From.replace('+', '').replace(':', '')}{ext}"
    
    try:
        # Secure Download from Twilio
        file_res = requests.get(MediaUrl0, auth=HTTPBasicAuth(TWILIO_SID, TWILIO_TOKEN))
        with open(filename, "wb") as f:
            f.write(file_res.content)

        # Process Resume
        data = ats.parse_resume(filename)

        # Terminal Dashboard View
        print(f"\n{'╔' + '═'*40 + '╗'}")
        print(f"║ WHATSAPP SUBMISSION: {data['name'].upper().ljust(18)} ║")
        print(f"║ Match: {str(data['score']).ljust(5)}% | Exp: {str(data['years_exp']).ljust(4)} Yrs ║")
        print(f"{'╚' + '═'*40 + '╝'}\n")

        # Response Logic
        if data['score'] > 75:
            status = "🚀 *Priority Match!* Our team will contact you shortly for an interview."
        elif data['score'] > 50:
            status = "✅ *Received.* Your profile is being reviewed by our technical lead."
        else:
            status = "📁 *Received.* We've added you to our pool for future opportunities."

        reply = (
            f"Hi {data['name']},\n\n{status}\n\n"
            f"📊 *Match Score:* {data['score']}%\n"
            f"⏳ *Experience:* {data['years_exp']} Yrs\n"
            f"🛠️ *Skills:* {', '.join(data['skills']) if data['skills'] else 'N/A'}"
        )
        twiml_resp.message(reply)

    except Exception as e:
        print(f"❌ Error: {e}")
        twiml_resp.message("⚠️ Sorry, I couldn't process that file. Please send a standard PDF.")
    finally:
        if os.path.exists(filename):
            os.remove(filename)

    return Response(content=str(twiml_resp), media_type="application/xml")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("twillio_parser:app", port=4000, reload=True)
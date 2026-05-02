# import spacy
# from sentence_transformers import SentenceTransformer, util
# from datetime import datetime
# import re


# class CompanyExtractor:

#     def __init__(self):

#         self.nlp = spacy.load("en_core_web_sm")
#         self.embedder = SentenceTransformer("all-MiniLM-L6-v2")

#         self.company_anchor = self.embedder.encode(
#             ["company", "worked at", "employed at", "joined", "experience at"],
#             convert_to_tensor=True
#         )

#         self.noise_anchor = self.embedder.encode(
#             ["award", "skills", "education", "certification",
#             "project", "course", "training", "summary"],
#             convert_to_tensor=True
#         )

#     # -------------------------
#     # SCORE IF TEXT IS COMPANY CONTEXT
#     # -------------------------
#     def is_company_context(self, text):

#         emb = self.embedder.encode(text, convert_to_tensor=True)

#         company_score = util.cos_sim(emb, self.company_anchor).max().item()
#         noise_score = util.cos_sim(emb, self.noise_anchor).max().item()

#         return company_score > 0.35 and noise_score < 0.40

#     # -------------------------
#     # CLEAN COMPANY NAME (NEW)
#     # -------------------------
#     def clean_company(self, name):

#         name = re.sub(r"\s+", " ", name).strip()

#         # remove garbage symbols
#         name = re.sub(r"[^a-zA-Z0-9&.,\- ]", "", name)

#         return name.strip()

#     # -------------------------
#     # EXTRACT YEARS (NEW SMART PARSER)
#     # -------------------------
#     def extract_years(self, text):

#         patterns = [
#             r"(20\d{2}|19\d{2})\s*[-–to]{1,3}\s*(present|current|20\d{2}|19\d{2})",
#             r"(\d{1,2}/20\d{2})\s*[-–to]{1,3}\s*(present|current|\d{1,2}/20\d{2})"
#         ]

#         for p in patterns:
#             match = re.search(p, text, re.I)
#             if match:
#                 return match.groups()

#         return (None, None)

#     # -------------------------
#     # MAIN AI EXTRACTION (ENHANCED)
#     # -------------------------
#     def extract(self, text):

#         doc = self.nlp(text)

#         experience = []
#         seen = set()

#         dates = [ent.text for ent in doc.ents if ent.label_ == "DATE"]

#         for ent in doc.ents:

#             if ent.label_ != "ORG":
#                 continue

#             company = self.clean_company(ent.text)

#             if company in seen or len(company) < 2:
#                 continue

#             start = max(ent.start - 40, 0)
#             end = min(ent.end + 40, len(doc))
#             context = doc[start:end].text

#             if not self.is_company_context(context):
#                 continue

#             # -------- FIXED DATE LOGIC --------
#             start_year = None
#             end_year = None

#             for d in dates:
#                 y = re.findall(r"\d{4}", d)
#                 if y:
#                     if not start_year:
#                         start_year = int(y[0])
#                     else:
#                         end_year = int(y[0])

#             experience.append({
#                 "company": company,
#                 "tenure": (
#                     f"{start_year} - {'Present' if not end_year else end_year}"
#                     if start_year else "Unknown"
#                 ),
#                 "confidence": round(util.cos_sim(
#                     self.embedder.encode(company, convert_to_tensor=True),
#                     self.company_anchor
#                 ).max().item(), 2)
#             })

#             seen.add(company)

#         return {
#             "experience": experience[:6]
#         }

#     # -------------------------
#     # TOTAL EXPERIENCE (IMPROVED SAFE)
#     # -------------------------
#     def total_years(self, experience):

#         current = datetime.now().year
#         total = 0

#         for exp in experience:

#             try:
#                 tenure = exp.get("tenure", "Unknown")

#                 if "Unknown" in tenure:
#                     continue

#                 parts = tenure.split("-")

#                 start = int(re.findall(r"\d{4}", parts[0])[0])
#                 end_raw = parts[1].lower()

#                 end = current if "present" in end_raw else int(re.findall(r"\d{4}", parts[1])[0])

#                 total += max(0, end - start)

#             except:
#                 continue

#         return round(total, 1)
    
###############

import re
import spacy


class CompanyExtractor:

    def __init__(self):
        self.nlp = spacy.load("en_core_web_sm")

        self.roles = [
            "software engineer",
            "backend engineer",
            "frontend engineer",
            "data engineer",
            "developer",
            "intern",
            "manager",
            "analyst",
            "devops engineer"
        ]

    # -------------------------
    # COMPANY VALIDATION (FIXED)
    # -------------------------
    def is_real_company(self, text):

        t = text.strip()

        bad = [
            "software", "development", "engineering",
            "pipeline", "system", "web", "android",
            "resume", "enthusiast"
        ]

        low = t.lower()

        if any(b in low for b in bad):
            return False

        # allow acronyms like TCS, IBM, etc.
        if len(t) < 2:
            return False

        if not any(c.isalpha() for c in t):
            return False

        # avoid long garbage spans
        if len(t.split()) > 5:
            return False

        return True

    # -------------------------
    # ROLE EXTRACTION (context-based)
    # -------------------------
    def extract_role(self, sentence):

        s = sentence.lower()

        for r in self.roles:
            if r in s:
                return r.title()

        return "Unknown"

    # -------------------------
    # TENURE EXTRACTION (IMPROVED)
    # -------------------------
    def extract_tenure(self, sentence):

        # matches:
        # 2020 - 2023
        # 2020–Present
        # 2020 to 2023
        pattern = r"(19\d{2}|20\d{2})\s*(?:-|to|–)\s*(present|19\d{2}|20\d{2})"

        match = re.search(pattern, sentence, re.IGNORECASE)

        if match:
            return f"{match.group(1)} - {match.group(2)}"

        # fallback single year
        years = re.findall(r"(19\d{2}|20\d{2})", sentence)

        if years:
            return f"{years[0]} - Present"

        return "Unknown"

    # -------------------------
    # MAIN EXTRACTION (FIXED LOGIC)
    # -------------------------
    def extract(self, doc):

        experience = []
        seen = set()

        for sent in doc.sents:

            sentence = sent.text

            # extract ORGs from SAME sentence only (IMPORTANT FIX)
            orgs = [ent.text.strip() for ent in sent.ents if ent.label_ == "ORG"]

            if not orgs:
                continue

            role = self.extract_role(sentence)
            tenure = self.extract_tenure(sentence)

            for company in orgs:

                if not self.is_real_company(company):
                    continue

                key = company.lower()

                if key in seen:
                    continue

                experience.append({
                    "company": company,
                    "role": role,
                    "tenure": tenure
                })

                seen.add(key)

                if len(experience) >= 6:
                    return {"experience": experience}

        return {"experience": experience}
import re
from sentence_transformers import SentenceTransformer, util


class SkillMatcher:
    def __init__(self):

        self.embedder = SentenceTransformer("all-MiniLM-L6-v2")

        self.skill_bank = [
            "python", "java", "c++", "sql", "git", "github",
            "docker", "kubernetes", "aws", "azure", "gcp",
            "rest api", "apis",
            "data structures", "algorithms",
            "machine learning", "deep learning",
            "etl", "data pipelines",
            "system design", "microservices"
        ]

    def clean(self, text):
        return re.sub(r"[^a-z0-9+#. ]", " ", text.lower())

    # ---------------- ROLE DETECTION ----------------
    def detect_role(self, text):
        t = text.lower()

        if "data engineer" in t or "etl" in t:
            return "data_engineer"

        if "backend" in t or "api" in t:
            return "backend_engineer"

        if "frontend" in t or "react" in t:
            return "frontend_engineer"

        if "machine learning" in t:
            return "ml_engineer"

        return "software_engineer"

    # ---------------- ROLE WEIGHTS ----------------
    def role_weights(self, role):
        return {
            "backend_engineer": {
                "apis": 3,
                "microservices": 3,
                "java": 2,
                "python": 2
            },
            "data_engineer": {
                "etl": 3,
                "data pipelines": 3,
                "sql": 2
            },
            "ml_engineer": {
                "machine learning": 3,
                "python": 2
            }
        }.get(role, {})

    # ---------------- SKILL EXTRACTION ----------------
    def extract_skills(self, text):
        text = self.clean(text or "")
        return list({s for s in self.skill_bank if s in text})

    # ---------------- MATCH ENGINE ----------------
    def match_skills_from_files(self, jd_text, resume_text):

        jd_text = jd_text or ""
        resume_text = resume_text or ""

        jd_skills = self.extract_skills(jd_text)
        resume_skills = self.extract_skills(resume_text)

        # SAFE GUARD
        if not jd_skills:
            return {
                "match_score": 0,
                "matched_skills": [],
                "missing_skills": [],
                "jd_skills": [],
                "resume_skills": resume_skills,
                "decision": "REJECT",
                "confidence": "low"
            }

        role = self.detect_role(jd_text)
        weights = self.role_weights(role)

        matched, missing = [], []
        score, total = 0, 0

        for skill in jd_skills:
            w = weights.get(skill, 1)
            total += w

            if skill in resume_skills:
                matched.append(skill)
                score += w
            else:
                missing.append(skill)

        match_score = round((score / total) * 100, 2)

        return {
            "role_detected": role,
            "match_score": match_score,
            "matched_skills": matched,
            "missing_skills": missing,
            "jd_skills": jd_skills,
            "resume_skills": resume_skills,
            "decision": "SHORTLIST" if match_score >= 65 else "REJECT",
            "confidence": "high" if match_score > 80 else "medium" if match_score > 60 else "low"
        }
    

############
import re
import spacy
from sentence_transformers import SentenceTransformer, util


class SkillMatcher:

    def __init__(self):
        self.embedder = SentenceTransformer("all-MiniLM-L6-v2")

        self.skills = [
            "software engineering",
            "backend development",
            "frontend development",
            "api development",
            "database design",
            "system design",
            "debugging",
            "testing",
            "software architecture",
            "code documentation",
            "data structures",
            "algorithms",
            "devops",
            "cloud computing",
            "microservices",
            "rest api",
        ]

        self.skill_embeddings = self.embedder.encode(
            self.skills,
            convert_to_tensor=True,
            normalize_embeddings=True
        )

        # spaCy for real phrase extraction
        self.nlp = spacy.load("en_core_web_sm")

    def extract_phrases(self, text):
        doc = self.nlp(text.lower())

        phrases = set()

        # noun chunks (high quality phrases)
        for chunk in doc.noun_chunks:
            chunk = chunk.text.strip()
            if 3 <= len(chunk) <= 40:
                phrases.add(chunk)

        # also add verb + noun patterns (e.g. "built api", "designed system")
        for token in doc:
            if token.pos_ in ["VERB"]:
                phrase = token.text + " " + " ".join([t.text for t in token.children if t.pos_ == "NOUN"])
                phrase = phrase.strip()
                if len(phrase.split()) <= 5:
                    phrases.add(phrase)

        return list(phrases)

    def extract_skills(self, text, threshold=0.55, top_k=3):

        phrases = self.extract_phrases(text)

        if not phrases:
            return []

        phrase_embeddings = self.embedder.encode(
            phrases,
            convert_to_tensor=True,
            normalize_embeddings=True
        )

        scores = util.cos_sim(phrase_embeddings, self.skill_embeddings)

        found = set()

        for i in range(len(phrases)):
            best_scores, best_idx = scores[i].topk(top_k)

            for score, idx in zip(best_scores, best_idx):
                score = float(score)

                if score >= threshold:
                    found.add(self.skills[int(idx)])

        return sorted(found)
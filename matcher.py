from sentence_transformers import SentenceTransformer, util

model = SentenceTransformer("all-MiniLM-L6-v2")


class Matcher:

    def compute_score(self, jd_text, resume_text):

        jd_emb = model.encode(jd_text)
        res_emb = model.encode(resume_text)

        return float(util.cos_sim(jd_emb, res_emb)[0][0] * 100)

    def skill_overlap(self, jd_skills, resume_skills):

        jd = set(jd_skills)
        rs = set(resume_skills)

        return {
            "match": list(jd & rs),
            "missing": list(jd - rs),
            "coverage": len(jd & rs) / max(len(jd), 1)
        }
from sentence_transformers import SentenceTransformer, util
import spacy

nlp = spacy.load("en_core_web_sm")
model = SentenceTransformer("all-MiniLM-L6-v2")


def extract_real_skills(text, jd_context=None, top_k=20):

    doc = nlp(text)

    candidates = []

    # 1. noun phrases only (important fix)
    for chunk in doc.noun_chunks:
        phrase = chunk.text.strip().lower()

        if len(phrase.split()) > 4:
            continue
        if any(char.isdigit() for char in phrase):
            continue
        if phrase in ["experience", "responsibilities", "job", "work"]:
            continue

        candidates.append(phrase)

    # 2. semantic filtering using JD (VERY IMPORTANT)
    if jd_context:
        jd_emb = model.encode(jd_context)

        scored = []
        for c in candidates:
            emb = model.encode(c)
            score = util.cos_sim(jd_emb, emb).item()
            scored.append((c, score))

        scored = sorted(scored, key=lambda x: x[1], reverse=True)

        return [s[0] for s in scored[:top_k]]

    return list(set(candidates))[:top_k]
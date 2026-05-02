from parser import read_file
from nlp_layer import NLPExtractor
from skill_graph import SkillGraph
from matcher import Matcher


class EightfoldStyleATS:

    def __init__(self):
        self.nlp = NLPExtractor()
        self.graph = SkillGraph()
        self.matcher = Matcher()

    def process(self, jd_path, resume_path):

        jd_text = read_file(jd_path)
        resume_text = read_file(resume_path)

        # NLP extraction
        jd_skills_raw = self.nlp.extract_skill_candidates(jd_text)
        resume_skills_raw = self.nlp.extract_skill_candidates(resume_text)

        # skill expansion (ontology)
        jd_skills = self.graph.expand_skills(jd_skills_raw)
        resume_skills = self.graph.expand_skills(resume_skills_raw)

        # matching
        score = self.matcher.compute_score(jd_text, resume_text)
        gap = self.matcher.skill_overlap(jd_skills, resume_skills)

        return {
            "jd_skills": jd_skills[:30],
            "resume_skills": resume_skills[:30],
            "match_score": round(score, 2),
            "gap_analysis": gap
        }
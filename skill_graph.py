class SkillGraph:

    def __init__(self):
        # simplified ontology (real systems have millions of nodes)
        self.graph = {
            "machine learning": ["ml", "ai", "data science"],
            "python": ["django", "flask", "pandas"],
            "communication": ["presentation", "writing"],
            "leadership": ["team management", "mentoring"]
        }

    def expand_skills(self, skills):
        expanded = set(skills)

        for s in skills:
            if s in self.graph:
                expanded.update(self.graph[s])

        return list(expanded)
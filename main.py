from pipeline import EightfoldStyleATS

if __name__ == "__main__":

    # 🔴 PASS FILE PATHS HERE
    JD_PATH = "/home/credentek/Downloads/sample-job-description.pdf"
    RESUME_PATH = "/home/credentek/Downloads/functionalsample.pdf"

    ats = EightfoldStyleATS()

    result = ats.process(JD_PATH, RESUME_PATH)

    import json
    print(json.dumps(result, indent=4))
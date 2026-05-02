import os
import logging

os.environ["TF_CPP_MIN_LOG_LEVEL"] = "3"
os.environ["TOKENIZERS_PARALLELISM"] = "false"
os.environ["CUDA_VISIBLE_DEVICES"] = "-1"

logging.getLogger("tensorflow").setLevel(logging.ERROR)
logging.getLogger("transformers").setLevel(logging.ERROR)

from resume_parser import UniversalATSParser

JD_PATH = "/home/credentek/Downloads/software-engineer-job-description-D13502.png"
RESUME_PATH = "/home/credentek/Downloads/image (5).png"

def safe_join(items):
    return ", ".join(items) if items else "None"


ats = UniversalATSParser(jd_path=JD_PATH)

result = ats.parse(RESUME_PATH)

print("\n" + "=" * 70)
print("                 🚀 ATS RESULT")
print("=" * 70)

bio = result.get("biographical", {})

print(f"\n👤 Name   : {bio.get('name', 'Unknown')}")
print(f"📧 Email  : {bio.get('email', 'None')}")
print(f"📞 Phone  : {bio.get('phone', 'None')}")

print("\n🏢 EXPERIENCE")
for e in result.get("experience", []):
    print(f"  • {e.get('company')} | {e.get('role')} | {e.get('tenure')}")

print("\n🎓 EDUCATION")
for e in result.get("education", []):
    print(f"  • {e.get('institution')} | {e.get('years')}")

skills = result.get("skills", {})

print("\n🧠 JD Skills:", safe_join(skills.get("jd_skills")))
print("🧠 Resume Skills:", safe_join(skills.get("resume_skills")))
print("✔ Matched Skills:", safe_join(skills.get("matched")))
print("❌ Missing Skills:", safe_join(skills.get("missing")))

print("\n📊 ATS SCORE:", result.get("ats", {}).get("score", 0))
print("🎯 DECISION:", result.get("ats", {}).get("decision", "REJECT"))

print("\n" + "=" * 70 + "\n")
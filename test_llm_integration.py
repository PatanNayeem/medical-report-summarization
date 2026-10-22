"""Run: python test_llm_integration.py  (no network, no GPU, no HuggingFace token needed)."""
import os, tempfile
os.environ["HUGGINGFACE_API_TOKEN"] = ""

from rag_engine import MedicalSummarizerEngine, LLMClient, parse_llm_summary
from config import Config

REPORT = """DIAGNOSIS:
1. Essential Hypertension (Stage 1).
MEDICATIONS & TREATMENT PLAN:
- Lisinopril 10mg orally once daily in the morning.
VITAL SIGNS:
- Blood Pressure: 138/88 mmHg
- Heart Rate: 82 bpm
- Fasting Blood Glucose: 112 mg/dL
RECOMMENDATIONS & FOLLOW-UP:
- Repeat lipid panel in 90 days.
"""

class StubRAG:
    def query_context(self, report_id, question, full_text=""):
        return full_text[:500]

class FakeLLM:
    def __init__(self, reply): self.reply, self.last = reply, ""
    def generate(self, prompt, max_tokens=700):
        self.last = prompt
        return self.reply

GOOD = ('Sure! ```json\n{"executive_summary":"Patient with stage 1 hypertension.",'
        '"clinical_impression":["Hypertension"],"medications_and_treatments":"Lisinopril 10mg",'
        '"risk_factors_and_warnings":["Moderate risk"],"recommendations":["Repeat lipids in 90 days"]}\n```')

# 1. No token -> rule-based fallback, never crashes
s = MedicalSummarizerEngine(rag_engine=StubRAG(), llm=LLMClient()).generate_clinical_summary("r1", REPORT)
assert s["generated_by"] == "Rule-based extraction"
assert "96.4" not in str(s)
print("PASS 1 fallback when no token")

# 2. LLM JSON (wrapped in prose/code fence) is merged; numbers stay rule-based
s = MedicalSummarizerEngine(rag_engine=StubRAG(), llm=FakeLLM(GOOD)).generate_clinical_summary("r2", REPORT)
assert s["generated_by"].startswith("Mistral")
assert s["executive_summary"].startswith("Patient")
assert s["medications_and_treatments"] == ["Lisinopril 10mg"]
assert s["key_metrics"] and s["risk_level"] in ("High", "Moderate", "Low")
print("PASS 2 LLM output merged")

# 3. Bad model output never breaks the summary
for bad in [None, "", "no json", "{broken", '["a"]', '{"clinical_impression": 5}']:
    assert parse_llm_summary(bad) == {}, bad
s = MedicalSummarizerEngine(rag_engine=StubRAG(), llm=FakeLLM("{broken")).generate_clinical_summary("r3", REPORT)
assert s["generated_by"] == "Rule-based extraction"
print("PASS 3 bad output handled")

# 4. Q&A: grounded LLM answer, with template fallback
fake = FakeLLM("Lisinopril 10mg once daily.")
a = MedicalSummarizerEngine(rag_engine=StubRAG(), llm=fake).answer_patient_question("r4", REPORT, "What medications?")
assert a == "Lisinopril 10mg once daily." and "ONLY the report context" in fake.last
a2 = MedicalSummarizerEngine(rag_engine=StubRAG(), llm=FakeLLM(None)).answer_patient_question("r4", REPORT, "What medications?")
assert "medical report" in a2.lower()
print("PASS 4 Q&A with LLM and fallback")

# 5. PDF footer reports the true source
from pdf_generator import generate_medical_summary_pdf
import pypdf
Config.GENERATED_PDF_FOLDER = tempfile.mkdtemp()
s = MedicalSummarizerEngine(rag_engine=StubRAG(), llm=FakeLLM(GOOD)).generate_clinical_summary("r5", REPORT)
path = generate_medical_summary_pdf({"name": "T", "patient_code": "P1", "age": 1, "gender": "F", "blood_group": "A+"},
                                    {"filename": "x.txt"}, s, "t.pdf")
assert "Mistral-7B-Instruct" in pypdf.PdfReader(path).pages[0].extract_text()
print("PASS 5 PDF footer")
print("ALL TESTS PASSED")

import os
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from config import Config

def create_demo_pdf(filename, title, content_text):
    filepath = os.path.join(Config.UPLOAD_FOLDER, filename)
    doc = SimpleDocTemplate(filepath, pagesize=letter)
    styles = getSampleStyleSheet()
    
    title_style = ParagraphStyle('T', parent=styles['Heading1'], fontSize=16, leading=20, textColor='#0284C7')
    body_style = ParagraphStyle('B', parent=styles['Normal'], fontSize=10, leading=14)
    
    story = [
        Paragraph(f"<b>ST. JUDE MEDICAL CENTER - {title.upper()}</b>", title_style),
        Spacer(1, 12)
    ]
    
    for paragraph in content_text.split('\n\n'):
        story.append(Paragraph(paragraph.replace('\n', '<br/>'), body_style))
        story.append(Spacer(1, 8))
        
    doc.build(story)
    print(f"Created sample PDF: {filepath}")
    return filepath

if __name__ == "__main__":
    Config.init_app()
    
    # Report 1: Cardiology
    create_demo_pdf(
        "Cardiology_Report_John_Doe.pdf",
        "Cardiology Clinical Assessment",
        """Patient Name: John Doe | Age: 54 | Gender: Male | Patient Code: PAT-998231

CLINICAL IMPRESSION & CHIEF COMPLAINT:
Patient was evaluated for recurring substernal chest discomfort occurring during physical exertion over the last 2 weeks.

VITAL SIGNS & LAB FINDINGS:
- Blood Pressure: 142/90 mmHg (Stage 2 Hypertension)
- Heart Rate: 88 bpm
- Temperature: 98.4 °F
- Fasting Glucose: 128 mg/dL
- Total Cholesterol: 245 mg/dL | LDL: 158 mg/dL
- Cardiac Troponin I: < 0.01 ng/mL (Normal, no acute myocardial necrosis)

DIAGNOSIS:
1. Stable Angina Pectoris secondary to coronary artery disease.
2. Stage 2 Essential Hypertension.
3. Hypercholesterolemia.

MEDICATIONS & TREATMENT PLAN:
- Nitroglycerin 0.4mg sublingual tablets as needed for acute chest discomfort.
- Metoprolol Succinate 50mg orally once daily.
- Atorvastatin 40mg orally once daily.

RISK FACTORS & CLINICAL WARNINGS:
- High risk of ischemic cardiac events. Patient advised to seek emergency care if chest pain exceeds 10 minutes or fails to respond to Nitroglycerin.

RECOMMENDATIONS & FOLLOW-UP:
- Outpatient Coronary Angiography recommended within 14 days.
- Strict low-fat, low-sodium dietary regimen."""
    )
    
    # Report 2: MRI Brain
    create_demo_pdf(
        "MRI_Brain_Scan_Analysis.pdf",
        "Radiology & Neuro-Imaging Center",
        """Patient Name: Marcus Brody | Age: 62 | Gender: Male | Patient Code: PAT-441092

PROCEDURE: Multi-planar, multi-sequence MRI of the Brain with and without IV Contrast.

FINDINGS & IMPRESSION:
Ventricular system and extra-axial CSF spaces are within normal limits for age. No midline shift or mass effect identified.
Small scattered focal T2/FLAIR hyperintensities noted in the subcortical white matter, consistent with mild chronic small vessel ischemic changes.
No acute intracranial hemorrhage, restricted diffusion, or abnormal parenchymal enhancement detected.

DIAGNOSIS:
1. Mild Chronic Microvascular Ischemic Disease.
2. No acute intracranial infarct or space-occupying lesion.

MEDICATIONS & RECOMMENDATIONS:
- Aspirin 81mg orally daily for secondary vascular prophylaxis.
- Regular blood pressure and glycemic monitoring.
- Routine follow-up in 12 months unless neurological symptoms arise."""
    )

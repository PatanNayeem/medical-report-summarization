import os
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from datetime import datetime
from config import Config


def generate_medical_summary_pdf(patient_data, report_data, summary_data, output_filename):
    """Generate professional, printable clinical PDF medical report summary."""
    output_path = os.path.join(Config.GENERATED_PDF_FOLDER, output_filename)
    
    doc = SimpleDocTemplate(
        output_path,
        pagesize=letter,
        rightMargin=36,
        leftMargin=36,
        topMargin=36,
        bottomMargin=36
    )
    
    styles = getSampleStyleSheet()
    
    # Custom Styles
    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Heading1'],
        fontName='Helvetica-Bold',
        fontSize=20,
        leading=24,
        textColor=colors.HexColor('#0F172A')
    )
    
    subtitle_style = ParagraphStyle(
        'DocSubtitle',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=10,
        leading=12,
        textColor=colors.HexColor('#0284C7')
    )

    section_heading = ParagraphStyle(
        'SectionHeading',
        parent=styles['Heading2'],
        fontName='Helvetica-Bold',
        fontSize=13,
        leading=16,
        textColor=colors.HexColor('#1E293B'),
        spaceBefore=10,
        spaceAfter=6
    )

    body_style = ParagraphStyle(
        'BodyTextCustom',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=10,
        leading=14,
        textColor=colors.HexColor('#334155')
    )

    bold_body_style = ParagraphStyle(
        'BoldBodyCustom',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=10,
        leading=14,
        textColor=colors.HexColor('#0F172A')
    )

    story = []

    # Header / Hospital Branding
    header_table_data = [
        [
            Paragraph("<b>ST. JUDE MEDICAL CENTER & RESEARCH</b><br/><font size=8 color='#64748B'>AI Medical Analytics Division</font>", title_style),
            Paragraph(f"<b>CLINICAL SUMMARY REPORT</b><br/><font size=8 color='#64748B'>Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}</font>", subtitle_style)
        ]
    ]
    header_table = Table(header_table_data, colWidths=[4.25*inch, 3.25*inch])
    header_table.setStyle(TableStyle([
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('ALIGN', (1,0), (1,0), 'RIGHT'),
    ]))
    story.append(header_table)
    story.append(Spacer(1, 10))
    story.append(HRFlowable(width="100%", thickness=1.5, color=colors.HexColor('#0284C7'), spaceBefore=2, spaceAfter=12))

    # Patient Meta Box
    patient_info_data = [
        [
            Paragraph(f"<b>Patient Name:</b> {patient_data.get('name', 'N/A')}", body_style),
            Paragraph(f"<b>Patient Code:</b> {patient_data.get('patient_code', 'N/A')}", body_style),
            Paragraph(f"<b>Age / Gender:</b> {patient_data.get('age', 'N/A')} Yrs / {patient_data.get('gender', 'N/A')}", body_style)
        ],
        [
            Paragraph(f"<b>Blood Group:</b> {patient_data.get('blood_group', 'N/A')}", body_style),
            Paragraph(f"<b>Report File:</b> {report_data.get('filename', 'N/A')}", body_style),
            Paragraph(f"<b>Risk Status:</b> <font color='{'#DC2626' if summary_data.get('risk_level') == 'High' else '#EA580C' if summary_data.get('risk_level') == 'Moderate' else '#16A34A'}'><b>{summary_data.get('risk_level', 'Low').upper()} RISK</b></font>", body_style)
        ]
    ]
    info_table = Table(patient_info_data, colWidths=[2.5*inch, 2.5*inch, 2.5*inch])
    info_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#F8FAFC')),
        ('BOX', (0,0), (-1,-1), 1, colors.HexColor('#E2E8F0')),
        ('PADDING', (0,0), (-1,-1), 8),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
    ]))
    story.append(info_table)
    story.append(Spacer(1, 14))

    # Executive Briefing Section
    story.append(Paragraph("1. Executive Briefing", section_heading))
    story.append(Paragraph(summary_data.get('executive_summary', 'No summary available.'), body_style))
    story.append(Spacer(1, 10))

    # Clinical Impression & Findings
    story.append(Paragraph("2. Clinical Impression & Diagnoses", section_heading))
    impressions = summary_data.get('clinical_impression', [])
    if isinstance(impressions, list):
        for item in impressions:
            story.append(Paragraph(f"• {item}", body_style))
    else:
        story.append(Paragraph(str(impressions), body_style))
    story.append(Spacer(1, 10))

    # Vital Signs & Lab Parameters Table
    story.append(Paragraph("3. Vital Signs & Diagnostic Metrics", section_heading))
    metrics = summary_data.get('key_metrics', [])
    if metrics:
        metrics_table_data = [["Parameter Name", "Observed Value", "Unit / Status"]]
        for m in metrics:
            metrics_table_data.append([
                Paragraph(m.get('name', 'N/A'), body_style),
                Paragraph(f"<b>{m.get('value', 'N/A')}</b>", bold_body_style),
                Paragraph(m.get('unit', 'Normal'), body_style)
            ])
        metrics_table = Table(metrics_table_data, colWidths=[3.0*inch, 2.25*inch, 2.25*inch])
        metrics_table.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#0F172A')),
            ('TEXTCOLOR', (0,0), (-1,0), colors.white),
            ('BOTTOMPADDING', (0,0), (-1,0), 6),
            ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#CBD5E1')),
            ('PADDING', (0,0), (-1,-1), 6),
        ]))
        story.append(metrics_table)
    story.append(Spacer(1, 10))

    # Treatment & Medications
    story.append(Paragraph("4. Prescribed Medications & Treatment Plan", section_heading))
    meds = summary_data.get('medications_and_treatments', [])
    if isinstance(meds, list):
        for med in meds:
            story.append(Paragraph(f"• {med}", body_style))
    else:
        story.append(Paragraph(str(meds), body_style))
    story.append(Spacer(1, 10))

    # Risk Factors & Recommendations
    story.append(Paragraph("5. Critical Warnings & Clinical Recommendations", section_heading))
    recs = summary_data.get('recommendations', [])
    if isinstance(recs, list):
        for r in recs:
            story.append(Paragraph(f"• {r}", body_style))
    else:
        story.append(Paragraph(str(recs), body_style))
        
    story.append(Spacer(1, 24))

    # Footer & Doctor Signature Line
    sig_data = [
        [
            Paragraph("<b>AI Model Reference:</b> Mistral-7B + ChromaDB RAG", ParagraphStyle('F1', parent=body_style, fontSize=8, textColor=colors.HexColor('#94A3B8'))),
            Paragraph("<b>Attending Physician Signature:</b> ___________________________", ParagraphStyle('F2', parent=body_style, fontSize=9, alignment=2))
        ]
    ]
    sig_table = Table(sig_data, colWidths=[3.75*inch, 3.75*inch])
    sig_table.setStyle(TableStyle([
        ('VALIGN', (0,0), (-1,-1), 'BOTTOM'),
    ]))
    story.append(sig_table)

    doc.build(story)
    return output_path

from reportlab.lib.pagesizes import letter
from datetime import datetime
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image, KeepTogether
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.pdfgen import canvas
import os

class NumberedCanvas(canvas.Canvas):
    """
    Two-pass canvas to dynamically compute total pages and draw footer/header
    on every page.
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_page_decorations(num_pages)
            super().showPage()
        super().save()

    def draw_page_decorations(self, page_count):
        self.saveState()
        self.setFont("Helvetica", 8)
        self.setFillColor(colors.HexColor("#475569"))
        
        # Header (Only on page 2 onwards)
        if self._pageNumber > 1:
            self.drawString(54, 750, "Voice-Based Concept Understanding Analyser (VBCUA)")
            self.drawRightString(letter[0] - 54, 750, "AI Assessment Report")
            self.setStrokeColor(colors.HexColor("#cbd5e1"))
            self.setLineWidth(0.5)
            self.line(54, 742, letter[0] - 54, 742)
            
        # Footer (On all pages)
        self.setStrokeColor(colors.HexColor("#e2e8f0"))
        self.setLineWidth(0.5)
        self.line(54, 45, letter[0] - 54, 45)
        
        self.drawString(54, 32, "Confidential - For Educational Assessment Purposes Only")
        self.drawRightString(letter[0] - 54, 32, f"Page {self._pageNumber} of {page_count}")
        self.restoreState()

def generate_pdf_report(detail, plot_img_path, output_pdf_path):
    """
    Generates a beautifully styled PDF report using ReportLab.
    
    Parameters:
        detail (dict): The complete evaluation details dictionary (retrieved from database)
        plot_img_path (str): Path to the matplotlib plot image
        output_pdf_path (str): Target PDF file path
    """
    doc = SimpleDocTemplate(
        output_pdf_path,
        pagesize=letter,
        leftMargin=54,
        rightMargin=54,
        topMargin=54,
        bottomMargin=54
    )
    
    # Custom Palette
    c_primary = colors.HexColor("#1e3a8a")     # Slate Navy
    c_secondary = colors.HexColor("#475569")   # Dark Slate Grey
    c_neutral_light = colors.HexColor("#f8fafc") # Clean Off-White
    c_border = colors.HexColor("#cbd5e1")       # Subtle Light Blue-Grey
    
    # Accent color based on understanding level
    level = detail.get("understanding_level", "Moderate Understanding")
    if "Strong" in level:
        c_accent = colors.HexColor("#0f766e")  # Forest Teal
    elif "Moderate" in level:
        c_accent = colors.HexColor("#b45309")  # Amber Orange
    else:
        c_accent = colors.HexColor("#be123c")  # Crimson Red
        
    styles = getSampleStyleSheet()
    
    # Custom Paragraph Styles
    style_title = ParagraphStyle(
        'DocTitle',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=24,
        leading=28,
        textColor=c_primary,
        spaceAfter=4
    )
    
    style_subtitle = ParagraphStyle(
        'DocSubTitle',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=10,
        leading=14,
        textColor=c_secondary,
        spaceAfter=20
    )
    
    style_h1 = ParagraphStyle(
        'SectionH1',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=14,
        leading=18,
        textColor=c_primary,
        spaceBefore=15,
        spaceAfter=8,
        keepWithNext=True
    )
    
    style_body = ParagraphStyle(
        'BodyDark',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=9.5,
        leading=14,
        textColor=colors.HexColor("#0f172a")
    )
    
    style_body_bold = ParagraphStyle(
        'BodyDarkBold',
        parent=style_body,
        fontName='Helvetica-Bold'
    )
    
    style_score_val = ParagraphStyle(
        'ScoreVal',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=32,
        leading=36,
        textColor=c_accent,
        alignment=1 # Centered
    )
    
    style_score_lbl = ParagraphStyle(
        'ScoreLbl',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=9,
        leading=11,
        textColor=c_secondary,
        alignment=1 # Centered
    )
    
    style_table_header = ParagraphStyle(
        'TableHeader',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=9.5,
        leading=12,
        textColor=colors.white
    )
    
    style_bullet_strength = ParagraphStyle(
        'StrengthBullet',
        parent=style_body,
        leftIndent=15,
        firstLineIndent=-10,
        spaceAfter=4
    )

    story = []
    
    # ---------------- Header Banner ----------------
    story.append(Paragraph("Voice-Based Concept Understanding Analyser", style_title))
    story.append(Paragraph("AI-Generated Educational Spoken Concept Assessment & Performance Report", style_subtitle))
    
    # ---------------- Student & Session Info Table ----------------
    info_data = [
        [
            Paragraph("<b>Participant Name:</b>", style_body),
            Paragraph(detail.get("name", "N/A"), style_body),
            Paragraph("<b>Assessment Date:</b>", style_body),
            Paragraph(detail.get("evaluated_at", datetime.now().strftime("%Y-%m-%d %H:%M")), style_body)
        ],
        [
            Paragraph("<b>Target Concept:</b>", style_body),
            Paragraph(detail.get("concept_title", "N/A"), style_body),
            Paragraph("<b>Audio Duration:</b>", style_body),
            Paragraph(f"{detail.get('duration_sec', 0.0):.1f} seconds", style_body)
        ]
    ]
    
    # Width of letter is 612. Margins are 54*2=108. Usable width = 504.
    info_table = Table(info_data, colWidths=[110, 142, 110, 142])
    info_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), c_neutral_light),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('BOTTOMPADDING', (0,0), (-1,-1), 6),
        ('TOPPADDING', (0,0), (-1,-1), 6),
        ('LEFTPADDING', (0,0), (-1,-1), 8),
        ('RIGHTPADDING', (0,0), (-1,-1), 8),
        ('BOX', (0,0), (-1,-1), 0.5, c_border),
        ('INNERGRID', (0,0), (-1,-1), 0.5, c_border),
    ]))
    story.append(info_table)
    story.append(Spacer(1, 15))
    
    # ---------------- Executive Scores Section ----------------
    score_cards_data = [
        [
            Paragraph(f"{detail.get('overall_score', 0.0):.1f}/100", style_score_val),
            Paragraph(f"{detail.get('overall_score', 0.0):.1f}/100", style_score_val), # will replace below
            Paragraph(f"{detail.get('overall_score', 0.0):.1f}/100", style_score_val), # will replace below
        ],
        [
            Paragraph("OVERALL SCORE", style_score_lbl),
            Paragraph("CONCEPTUAL UNDERSTANDING", style_score_lbl),
            Paragraph("DELIVERY FLUENCY", style_score_lbl)
        ]
    ]
    
    # Calculate understanding and fluency subscores
    # To recover understanding and fluency subscores from detail:
    # We store overall_score in db. If we don't have separate subscores in db, we can approximate
    # or calculate. Wait, in database evaluation_results we store: overall_score, understanding_level.
    # In other tables we store similarity_score, pause_ratio, filler_ratio, word_count, duration.
    # We can reconstruct subscores exactly using the scoring_engine formula!
    # Let's import calculate_scores inside report generator to reconstruct if needed, or simply extract from database row.
    # Actually, let's reconstruct since we have all the raw metrics:
    # similarity_score, pause_ratio, filler_ratio (or filler_count, total_words), duration_sec, total_words.
    try:
        from scoring_engine import calculate_scores
        # Retrieve raw inputs
        sim_val = detail.get("similarity_score", 0.0)
        # Check keyword coverage. The semantic_eval checks coverage, but wait: we didn't store
        # keyword coverage ratio directly in the database schemas of the ERD!
        # Ah! Let's check: the ERD has `semantic_similarities` with `similarity_score` but no coverage.
        # But wait! We can compute keyword coverage by parsing the stored reference concept,
        # decoding its keywords, and checking them in the transcript text!
        # This is extremely simple and works perfectly because the transcript and reference text are stored!
        from concepts import decode_concept_text
        from semantic_eval import evaluate_keyword_coverage
        
        ref_text = detail.get("reference_text", "")
        clean_ref, keywords = decode_concept_text(ref_text)
        trans_text = detail.get("transcript_text", "")
        coverage_res = evaluate_keyword_coverage(trans_text, keywords)
        cov_val = coverage_res["coverage_ratio"]
        
        # Now run scoring engine
        scores = calculate_scores(
            semantic_similarity=sim_val,
            keyword_coverage=cov_val,
            pause_ratio=detail.get("pause_ratio", 0.0),
            filler_count=detail.get("filler_word_count", 0),
            duration_sec=detail.get("duration_sec", 1.0),
            word_count=detail.get("total_words", 0)
        )
        comp_score_str = f"{scores['comprehension_score']:.1f}/100"
        flue_score_str = f"{scores['fluency_score']:.1f}/100"
    except Exception:
        comp_score_str = "N/A"
        flue_score_str = "N/A"
        
    score_cards_data = [
        [
            Paragraph(f"{detail.get('overall_score', 0.0):.1f}/100", style_score_val),
            Paragraph(comp_score_str, style_score_val),
            Paragraph(flue_score_str, style_score_val),
        ],
        [
            Paragraph("OVERALL SCORE", style_score_lbl),
            Paragraph("CONCEPT COHERENCE", style_score_lbl),
            Paragraph("SPEAKING FLUENCY", style_score_lbl)
        ]
    ]
    
    score_table = Table(score_cards_data, colWidths=[168, 168, 168])
    score_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), c_neutral_light),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('BOTTOMPADDING', (0,0), (-1,-1), 10),
        ('TOPPADDING', (0,0), (-1,-1), 10),
        ('BOX', (0,0), (-1,-1), 1.0, c_accent),
        ('LINEBEFORE', (1,0), (1,1), 0.5, c_border),
        ('LINEBEFORE', (2,0), (2,1), 0.5, c_border),
    ]))
    story.append(score_table)
    
    # Level Callout Banner
    story.append(Spacer(1, 10))
    level_banner_data = [[
        Paragraph(f"<b>UNDERSTANDING LEVEL: {level.upper()}</b>", ParagraphStyle(
            'LBanner', parent=style_body_bold, alignment=1, textColor=colors.white, fontSize=10.5
        ))
    ]]
    level_table = Table(level_banner_data, colWidths=[504])
    level_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), c_accent),
        ('TOPPADDING', (0,0), (-1,-1), 6),
        ('BOTTOMPADDING', (0,0), (-1,-1), 6),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
    ]))
    story.append(level_table)
    story.append(Spacer(1, 15))
    
    # ---------------- Core Metrics Table ----------------
    story.append(Paragraph("Acoustic & NLP Evaluation Metrics", style_h1))
    
    # Gather raw metrics
    avg_rms = detail.get("rms_energy", 0.0)
    wpm = int((detail.get("total_words", 0) / detail.get("duration_sec", 1.0)) * 60) if detail.get("duration_sec", 0) > 0 else 0
    filler_count = detail.get("filler_word_count", 0)
    filler_ratio = detail.get("filler_ratio", 0.0)
    pause_ratio = detail.get("pause_ratio", 0.0)
    
    metrics_data = [
        [
            Paragraph("Metric Component", style_table_header),
            Paragraph("Analyzed Value", style_table_header),
            Paragraph("Benchmark Target", style_table_header),
            Paragraph("Diagnostic Status", style_table_header),
        ],
        [
            Paragraph("Semantic Similarity", style_body),
            Paragraph(f"{detail.get('similarity_score', 0.0):.3f}", style_body),
            Paragraph(">= 0.700 (High Alignment)", style_body),
            Paragraph("Strong Coherence" if detail.get('similarity_score', 0.0) >= 0.7 else "Moderate Coherence" if detail.get('similarity_score', 0.0) >= 0.45 else "Weak Coherence", style_body_bold)
        ],
        [
            Paragraph("Keyword Concept Coverage", style_body),
            Paragraph(f"{cov_val * 100:.1f}%" if 'cov_val' in locals() else "N/A", style_body),
            Paragraph(">= 70% of core terms", style_body),
            Paragraph("Satisfactory" if ('cov_val' in locals() and cov_val >= 0.7) else "Incomplete", style_body_bold)
        ],
        [
            Paragraph("Speaking Pace", style_body),
            Paragraph(f"{wpm} Words / Min", style_body),
            Paragraph("110 - 150 WPM (Normal)", style_body),
            Paragraph("Optimal" if 110 <= wpm <= 150 else "Slow" if wpm < 110 else "Fast", style_body_bold)
        ],
        [
            Paragraph("Pause & Hesitation Ratio", style_body),
            Paragraph(f"{pause_ratio * 100:.1f}%", style_body),
            Paragraph("10.0% - 25.0% (Natural)", style_body),
            Paragraph("Optimal" if 0.10 <= pause_ratio <= 0.25 else "Excessive Pauses" if pause_ratio > 0.25 else "Rushed Speech", style_body_bold)
        ],
        [
            Paragraph("Filler Word Ratio", style_body),
            Paragraph(f"{filler_count} words ({filler_ratio * 100:.1f}%)", style_body),
            Paragraph("<= 2.0% filler words", style_body),
            Paragraph("Low Fillers" if filler_ratio <= 0.02 else "High Fillers", style_body_bold)
        ],
        [
            Paragraph("Confidence (RMS Energy)", style_body),
            Paragraph(f"{avg_rms:.4f}", style_body),
            Paragraph("0.020 - 0.250 (Variable)", style_body),
            Paragraph("Confident Volume" if avg_rms >= 0.04 else "Low Volume / Soft Spoken", style_body_bold)
        ]
    ]
    
    metrics_table = Table(metrics_data, colWidths=[150, 110, 134, 110])
    metrics_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), c_primary),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('BOTTOMPADDING', (0,0), (-1,-1), 5),
        ('TOPPADDING', (0,0), (-1,-1), 5),
        ('LEFTPADDING', (0,0), (-1,-1), 6),
        ('RIGHTPADDING', (0,0), (-1,-1), 6),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, c_neutral_light]),
        ('BOX', (0,0), (-1,-1), 0.5, c_border),
        ('INNERGRID', (0,0), (-1,-1), 0.5, c_border),
    ]))
    story.append(metrics_table)
    story.append(Spacer(1, 15))
    
    # ---------------- Speech Transcription & Reference Section ----------------
    # Let's clean the reference concept text by removing the encoded keywords for PDF rendering
    ref_explanation, _ = decode_concept_text(detail.get("reference_text", ""))
    
    text_comparison_data = [
        [
            Paragraph("<b>Target Reference Explanation:</b>", style_body_bold),
            Paragraph("<b>Spoken Transcript:</b>", style_body_bold),
        ],
        [
            Paragraph(ref_explanation, style_body),
            Paragraph(detail.get("transcript_text", "No speech transcribed."), style_body),
        ]
    ]
    text_table = Table(text_comparison_data, colWidths=[246, 246])
    text_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), c_neutral_light),
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('BOTTOMPADDING', (0,0), (-1,-1), 8),
        ('TOPPADDING', (0,0), (-1,-1), 8),
        ('LEFTPADDING', (0,0), (-1,-1), 8),
        ('RIGHTPADDING', (0,0), (-1,-1), 8),
        ('BOX', (0,0), (-1,-1), 0.5, c_border),
        ('INNERGRID', (0,0), (-1,-1), 0.5, c_border),
    ]))
    story.append(KeepTogether([
        Paragraph("Speech Transcript vs. Concept Reference", style_h1),
        text_table
    ]))
    story.append(Spacer(1, 15))
    
    # ---------------- Acoustic Waveform Image ----------------
    if plot_img_path and os.path.exists(plot_img_path):
        waveform_img = Image(plot_img_path, width=480, height=216)
        waveform_img.hAlign = 'CENTER'
        story.append(KeepTogether([
            Paragraph("Acoustic Waveform & Pause Segmentation", style_h1),
            waveform_img
        ]))
        story.append(Spacer(1, 15))
        
    # ---------------- Actionable Coaching Insights ----------------
    feedback_elements = []
    
    # Recover coaching feedback lists from scoring engine
    if 'scores' in locals():
        strengths_list = scores["strengths"]
        improvements_list = scores["improvements"]
        recs_list = scores["recommendations"]
    else:
        strengths_list = ["Demonstrated fundamental spoken explanations of the topic."]
        improvements_list = ["Pacing and keyword delivery can be optimized."]
        recs_list = ["Review the reference concept text and practice speaking at a steady rate."]
        
    if strengths_list:
        feedback_elements.append(Paragraph("<b>Key Strengths:</b>", style_body_bold))
        for strength in strengths_list:
            feedback_elements.append(Paragraph(f"• {strength}", style_bullet_strength))
        feedback_elements.append(Spacer(1, 6))
        
    if improvements_list:
        feedback_elements.append(Paragraph("<b>Areas for Improvement:</b>", style_body_bold))
        for imp in improvements_list:
            feedback_elements.append(Paragraph(f"• {imp}", style_bullet_strength))
        feedback_elements.append(Spacer(1, 6))
        
    if recs_list:
        feedback_elements.append(Paragraph("<b>Actionable Recommendations & Next Steps:</b>", style_body_bold))
        for rec in recs_list:
            feedback_elements.append(Paragraph(f"• {rec}", style_bullet_strength))
            
    story.append(KeepTogether([
        Paragraph("AI-Powered Speech Coaching & Feedback", style_h1),
        Table([[feedback_elements]], colWidths=[504], style=TableStyle([
            ('BACKGROUND', (0,0), (-1,-1), c_neutral_light),
            ('BOX', (0,0), (-1,-1), 0.5, c_border),
            ('TOPPADDING', (0,0), (-1,-1), 10),
            ('BOTTOMPADDING', (0,0), (-1,-1), 10),
            ('LEFTPADDING', (0,0), (-1,-1), 12),
            ('RIGHTPADDING', (0,0), (-1,-1), 12),
        ]))
    ]))
    
    # Build document
    doc.build(story, canvasmaker=NumberedCanvas)

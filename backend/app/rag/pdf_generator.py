import io
from datetime import datetime
from typing import List, Dict, Any
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable

def generar_dictamen_pdf(titulo: str, mensajes: List[Dict[str, str]], usuario_nombre: str) -> io.BytesIO:
    """
    Genera un archivo PDF profesional y elegante con el dictamen de AmmayIA.
    """
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=40,
        leftMargin=40,
        topMargin=40,
        bottomMargin=40
    )

    styles = getSampleStyleSheet()

    # Estilos personalizados
    header_title_style = ParagraphStyle(
        'HeaderTitle',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=20,
        leading=24,
        textColor=colors.HexColor('#0f172a'),
        alignment=1
    )

    header_sub_style = ParagraphStyle(
        'HeaderSub',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=11,
        leading=14,
        textColor=colors.HexColor('#d97706'),
        alignment=1
    )

    meta_style = ParagraphStyle(
        'MetaStyle',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=9,
        leading=12,
        textColor=colors.HexColor('#64748b'),
        alignment=1
    )

    speaker_user_style = ParagraphStyle(
        'SpeakerUser',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=11,
        leading=14,
        textColor=colors.HexColor('#1d4ed8')
    )

    speaker_bot_style = ParagraphStyle(
        'SpeakerBot',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=11,
        leading=14,
        textColor=colors.HexColor('#b45309')
    )

    body_style = ParagraphStyle(
        'BodyDark',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=10,
        leading=14,
        textColor=colors.HexColor('#1e293b')
    )

    story = []

    # Cabecera
    story.append(Paragraph("⚖️ AMMAIA — DICTAMEN JURÍDICO", header_title_style))
    story.append(Paragraph("Inteligencia Artificial Especializada en Derecho Español & CENDOJ", header_sub_style))
    story.append(Spacer(1, 6))
    
    fecha_actual = datetime.now().strftime("%d/%m/%Y %H:%M")
    story.append(Paragraph(f"<b>Letrado/a:</b> {usuario_nombre} &nbsp;|&nbsp; <b>Fecha:</b> {fecha_actual} &nbsp;|&nbsp; <b>Asunto:</b> {titulo}", meta_style))
    story.append(Spacer(1, 10))
    story.append(HRFlowable(width="100%", thickness=1.5, color=colors.HexColor('#f59e0b'), spaceBefore=2, spaceAfter=14))

    # Contenido de la conversación
    for msg in mensajes:
        rol = msg.get("role", "user")
        raw_text = msg.get("content", "")
        
        # Limpieza de Markdown básico para reportlab
        clean_text = raw_text.replace("<", "&lt;").replace(">", "&gt;").replace("\n", "<br/>")

        if rol in ["user", "usuario"]:
            story.append(Paragraph("👤 CONSULTA DEL LETRADO:", speaker_user_style))
            story.append(Spacer(1, 4))
            story.append(Paragraph(clean_text, body_style))
            story.append(Spacer(1, 10))
        else:
            story.append(Paragraph("⚖️ DICTAMEN Y FUNDAMENTACIÓN LEGAL (AMMAIA):", speaker_bot_style))
            story.append(Spacer(1, 4))
            story.append(Paragraph(clean_text, body_style))
            story.append(Spacer(1, 14))

        story.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor('#cbd5e1'), spaceBefore=4, spaceAfter=10))

    # Pie de página
    story.append(Spacer(1, 10))
    story.append(Paragraph("<i>Documento generado con base en el BOE, Códigos Consolidados de España y Jurisprudencia de CENDOJ / Tribunal Supremo.</i>", meta_style))

    doc.build(story)
    buffer.seek(0)
    return buffer

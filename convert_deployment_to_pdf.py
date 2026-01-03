"""
Convert Deployment & Testing documentation to PDF
"""
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Preformatted, PageBreak
from reportlab.lib.enums import TA_LEFT, TA_JUSTIFY
from reportlab.lib.colors import HexColor
from pathlib import Path
import re
import sys

def parse_markdown_to_pdf(md_file, pdf_file):
    """Convert markdown to PDF with basic formatting"""
    
    # Read markdown file
    with open(md_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Create PDF
    doc = SimpleDocTemplate(
        str(pdf_file),
        pagesize=A4,
        rightMargin=72,
        leftMargin=72,
        topMargin=72,
        bottomMargin=72
    )
    
    # Styles
    styles = getSampleStyleSheet()
    
    # Custom styles
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        textColor=HexColor('#2c3e50'),
        spaceAfter=30,
        spaceBefore=20,
    )
    
    heading1_style = ParagraphStyle(
        'CustomHeading1',
        parent=styles['Heading1'],
        fontSize=18,
        textColor=HexColor('#2c3e50'),
        spaceAfter=12,
        spaceBefore=16,
    )
    
    heading2_style = ParagraphStyle(
        'CustomHeading2',
        parent=styles['Heading2'],
        fontSize=14,
        textColor=HexColor('#34495e'),
        spaceAfter=10,
        spaceBefore=14,
    )
    
    heading3_style = ParagraphStyle(
        'CustomHeading3',
        parent=styles['Heading3'],
        fontSize=12,
        textColor=HexColor('#34495e'),
        spaceAfter=8,
        spaceBefore=12,
    )
    
    heading4_style = ParagraphStyle(
        'CustomHeading4',
        parent=styles['Heading3'],
        fontSize=11,
        textColor=HexColor('#34495e'),
        spaceAfter=6,
        spaceBefore=10,
    )
    
    normal_style = ParagraphStyle(
        'CustomNormal',
        parent=styles['Normal'],
        fontSize=10,
        leading=14,
        alignment=TA_JUSTIFY,
        spaceAfter=6,
    )
    
    code_style = ParagraphStyle(
        'Code',
        parent=styles['Code'],
        fontSize=8,
        leading=10,
        leftIndent=20,
        spaceAfter=10,
        spaceBefore=10,
        textColor=HexColor('#333333'),
    )
    
    # Parse content
    story = []
    lines = content.split('\n')
    i = 0
    in_code_block = False
    code_lines = []
    
    while i < len(lines):
        line = lines[i]
        
        # Code blocks
        if line.strip().startswith('```'):
            if in_code_block:
                # End code block
                if code_lines:
                    code_text = '\n'.join(code_lines)
                    # Escape special characters for Preformatted
                    code_text = code_text.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
                    story.append(Preformatted(code_text, code_style))
                    code_lines = []
                in_code_block = False
            else:
                # Start code block
                in_code_block = True
            i += 1
            continue
        
        if in_code_block:
            code_lines.append(line)
            i += 1
            continue
        
        # Skip empty lines
        if not line.strip():
            if story:  # Add spacer only if we have content
                story.append(Spacer(1, 0.1*inch))
            i += 1
            continue
        
        # Horizontal rule
        if line.strip() == '---':
            story.append(Spacer(1, 0.2*inch))
            i += 1
            continue
        
        # Headers
        if line.startswith('#### '):
            text = line[5:].strip()
            text = escape_for_paragraph(text)
            story.append(Paragraph(text, heading4_style))
        elif line.startswith('### '):
            text = line[4:].strip()
            text = escape_for_paragraph(text)
            story.append(Paragraph(text, heading3_style))
        elif line.startswith('## '):
            text = line[3:].strip()
            text = escape_for_paragraph(text)
            story.append(Paragraph(text, heading2_style))
        elif line.startswith('# '):
            text = line[2:].strip()
            text = escape_for_paragraph(text)
            story.append(Paragraph(text, title_style))
        # Bold text or list items
        elif line.strip().startswith('- ') or line.strip().startswith('* ') or line.strip().startswith('✅') or line.strip().startswith('❌') or line.strip().startswith('⚠️') or line.strip().startswith('🔄'):
            text = escape_for_paragraph(line.strip())
            story.append(Paragraph(text, normal_style))
        # Tables (simple handling)
        elif '|' in line and not line.strip().startswith('|---'):
            text = escape_for_paragraph(line.strip())
            story.append(Paragraph(text, normal_style))
        # Normal paragraph
        else:
            text = escape_for_paragraph(line.strip())
            if text:  # Only add non-empty paragraphs
                story.append(Paragraph(text, normal_style))
        
        i += 1
    
    # Build PDF
    doc.build(story)
    print(f"✅ Created: {pdf_file}")

def escape_for_paragraph(text):
    """Escape special XML characters for ReportLab"""
    # Replace special characters
    text = text.replace('&', '&amp;')
    text = text.replace('<', '&lt;')
    text = text.replace('>', '&gt;')
    
    # Convert markdown bold to ReportLab bold
    text = re.sub(r'\*\*(.*?)\*\*', r'<b>\1</b>', text)
    
    # Convert markdown code to monospace
    text = re.sub(r'`(.*?)`', r'<font name="Courier">\1</font>', text)
    
    return text

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python convert_deployment_to_pdf.py <input.md> <output.pdf>")
        sys.exit(1)
    
    md_file = Path(sys.argv[1])
    pdf_file = Path(sys.argv[2])
    
    if not md_file.exists():
        print(f"❌ File not found: {md_file}")
        sys.exit(1)
    
    try:
        parse_markdown_to_pdf(md_file, pdf_file)
        print(f"\n✨ Conversion complete!")
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

"""
Convert Markdown documentation to PDF using ReportLab
"""
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Preformatted, PageBreak
from reportlab.lib.enums import TA_LEFT, TA_JUSTIFY
from reportlab.lib.colors import HexColor
from pathlib import Path
import re

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
                    # Split long lines
                    formatted_code = []
                    for code_line in code_text.split('\n'):
                        if len(code_line) > 85:
                            # Break long lines
                            while len(code_line) > 85:
                                formatted_code.append(code_line[:85])
                                code_line = '  ' + code_line[85:]
                            if code_line:
                                formatted_code.append(code_line)
                        else:
                            formatted_code.append(code_line)
                    
                    code_text = '\n'.join(formatted_code)
                    pre = Preformatted(code_text, code_style)
                    story.append(pre)
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
            if story:  # Add spacer only if there's content
                story.append(Spacer(1, 0.1*inch))
            i += 1
            continue
        
        # Headers
        if line.startswith('# '):
            text = line[2:].strip()
            story.append(Paragraph(text, title_style))
        elif line.startswith('## '):
            text = line[3:].strip()
            story.append(Paragraph(text, heading1_style))
        elif line.startswith('### '):
            text = line[4:].strip()
            story.append(Paragraph(text, heading2_style))
        elif line.startswith('#### '):
            text = line[5:].strip()
            story.append(Paragraph(text, heading3_style))
        # Lists
        elif line.strip().startswith('- ') or line.strip().startswith('* '):
            text = '• ' + line.strip()[2:]
            # Handle inline code
            text = re.sub(r'`([^`]+)`', r'<font face="Courier" color="#c7254e">\1</font>', text)
            # Handle bold
            text = re.sub(r'\*\*([^*]+)\*\*', r'<b>\1</b>', text)
            # Handle checkmarks and crosses
            text = text.replace('✅', '✓').replace('❌', '✗')
            story.append(Paragraph(text, normal_style))
        # Numbered lists
        elif re.match(r'^\d+\.\s', line.strip()):
            match = re.match(r'^(\d+)\.\s(.+)', line.strip())
            if match:
                num, text = match.groups()
                text = f'{num}. {text}'
                # Handle inline code
                text = re.sub(r'`([^`]+)`', r'<font face="Courier" color="#c7254e">\1</font>', text)
                # Handle bold
                text = re.sub(r'\*\*([^*]+)\*\*', r'<b>\1</b>', text)
                story.append(Paragraph(text, normal_style))
        # Regular paragraphs
        else:
            text = line.strip()
            # Handle inline code
            text = re.sub(r'`([^`]+)`', r'<font face="Courier" color="#c7254e">\1</font>', text)
            # Handle bold
            text = re.sub(r'\*\*([^*]+)\*\*', r'<b>\1</b>', text)
            # Handle checkmarks and crosses
            text = text.replace('✅', '✓').replace('❌', '✗')
            
            if text:
                story.append(Paragraph(text, normal_style))
        
        i += 1
    
    # Build PDF
    doc.build(story)
    print(f"✅ Created: {pdf_file}")

if __name__ == "__main__":
    base_path = Path(__file__).parent
    
    # Convert all three documents
    files = [
        ("docs_before_jwt.md", "1_Dokumentasi_API_Sebelum_JWT.pdf"),
        ("docs_after_jwt.md", "2_Dokumentasi_API_Setelah_JWT.pdf"),
        ("installation_usage_guide.md", "3_Panduan_Instalasi_dan_Penggunaan.pdf")
    ]
    
    print("Converting markdown files to PDF...\n")
    
    for md_file, pdf_file in files:
        md_path = base_path / md_file
        pdf_path = base_path / pdf_file
        
        if md_path.exists():
            try:
                parse_markdown_to_pdf(md_path, pdf_path)
            except Exception as e:
                print(f"❌ Error converting {md_file}: {e}")
                import traceback
                traceback.print_exc()
        else:
            print(f"⚠️  File not found: {md_file}")
    
    print("\n✨ Conversion complete!")

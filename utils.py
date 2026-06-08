import fitz
from docx import Document

def extract_text(uploaded_file):
    name = uploaded_file.name
    if name.endswith('.txt'):
        return uploaded_file.read().decode('utf-8')
    elif name.endswith('.docx'):
        doc = Document(uploaded_file)
        return '\n'.join([p.text for p in doc.paragraphs])
    elif name.endswith('.pdf'):
        doc = fitz.open(stream=uploaded_file.read(), filetype="pdf")
        return ''.join([page.get_text() for page in doc])
    else:
        return None
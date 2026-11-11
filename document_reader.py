
import fitz
from docx import Document

def extract_text_from_pdf(uploaded_file):
    pdf_bytes = uploaded_file.getvalue()
    pdf_document = fitz.open(stream=pdf_bytes, filetype="pdf")
    pages = []

    for page_number, page in enumerate(pdf_document, start=1):
        text = page.get_text("text")

        if text.strip():
            pages.append({
                "page": page_number,
                "content": text.strip()
            })

    pdf_document.close()
    return pages


def extract_text_from_docx(uploaded_file):
    document = Document(uploaded_file)

    paragraphs = [
        paragraph.text.strip()
        for paragraph in document.paragraphs
        if paragraph.text.strip()
    ]

    full_text = "\n".join(paragraphs)

    if not full_text:
        return []

    return [{
        "page": 1,
        "content": full_text
    }]


def extract_text(uploaded_file):
    filename = uploaded_file.name.lower()

    if filename.endswith(".pdf"):
        return extract_text_from_pdf(uploaded_file)

    elif filename.endswith(".docx"):
        return extract_text_from_docx(uploaded_file)

    else:
        raise ValueError("Unsupported file format. Upload PDF or DOCX.")

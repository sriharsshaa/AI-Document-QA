import fitz


def extract_pages_from_pdf(file_path: str):
    document = fitz.open(file_path)

    pages = []

    for page_number, page in enumerate(document, start=1):

        # Try normal PDF text extraction
        text = page.get_text("text").strip()

        # Clean excessive whitespace
        text = " ".join(text.split())

        if text:
            pages.append({
                "page": page_number,
                "text": text
            })

    document.close()

    return pages
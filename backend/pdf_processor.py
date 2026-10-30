import logging
import fitz


logger = logging.getLogger(__name__)


def extract_pages_from_pdf(file_path: str):
    """
    Extract selectable text from every page of a PDF.

    Returns:
        [
            {
                "page": 1,
                "text": "Extracted page text"
            }
        ]

    Note:
        Scanned PDFs require OCR, which is not implemented here.
    """

    pages = []

    try:

        with fitz.open(file_path) as document:

            if document.is_encrypted:

                if not document.authenticate(""):
                    raise ValueError(
                        "Password-protected PDFs are not supported."
                    )

            if len(document) == 0:
                raise ValueError(
                    "The uploaded PDF contains no pages."
                )

            for page_number, page in enumerate(
                document,
                start=1
            ):

                # Extract text from the current page.
                text = page.get_text("text")

                # Normalize whitespace.
                text = " ".join(text.split())

                if text:

                    pages.append({
                        "page": page_number,
                        "text": text
                    })

                else:

                    logger.warning(
                        "No selectable text found on page %s",
                        page_number
                    )

        logger.info(
            "Extracted text from %s of %s PDF pages",
            len(pages),
            page_number if 'page_number' in locals() else 0
        )

        return pages

    except fitz.FileDataError as error:

        logger.exception("Invalid or corrupted PDF.")

        raise ValueError(
            "The uploaded PDF is corrupted or invalid."
        ) from error

    except Exception:

        logger.exception("PDF text extraction failed.")

        raise
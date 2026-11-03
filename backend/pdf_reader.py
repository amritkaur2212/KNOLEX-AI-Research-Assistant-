
import fitz
from pathlib import Path


def read_pdf(file_path: str) -> list[dict]:
    """
    Extract text from each page of a PDF.

    Returns:
        A list containing each page's number and extracted text.
    """
    path = Path(file_path)

    if not path.exists():
        raise FileNotFoundError(f"PDF file not found: {path}")

    pages = []

    try:
        with fitz.open(str(path)) as pdf:
            if pdf.is_encrypted:
                raise ValueError(
                    "This PDF is password-protected. "
                    "Please upload an unlocked PDF."
                )

            for page_number, page in enumerate(pdf, start=1):
                text = page.get_text("text").strip()

                pages.append({
                    "page": page_number,
                    "text": text
                })

    except fitz.FileDataError as exc:
        raise ValueError(
            "The uploaded file is not a valid or readable PDF."
        ) from exc

    return pages

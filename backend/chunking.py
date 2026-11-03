
from langchain_text_splitters import RecursiveCharacterTextSplitter


def create_chunks(pages: list[dict]) -> list[dict]:
    """
    Split extracted PDF pages into smaller text chunks.

    Each chunk retains its original page number.
    """
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=500,
        chunk_overlap=100,
        separators=["\n\n", "\n", ". ", " ", ""],
    )

    chunks = []

    for page in pages:
        text = page.get("text", "").strip()

        if not text:
            continue

        page_number = page.get("page", "Unknown")

        page_chunks = splitter.split_text(text)

        for chunk in page_chunks:
            chunks.append({
                "text": chunk,
                "page": page_number,
            })

    return chunks

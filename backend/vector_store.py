
from pathlib import Path
import hashlib

import chromadb


# Store the database inside the backend folder.
BASE_DIR = Path(__file__).resolve().parent
CHROMA_DIR = BASE_DIR / "chroma_db"

CHROMA_DIR.mkdir(parents=True, exist_ok=True)

client = chromadb.PersistentClient(path=str(CHROMA_DIR))

collection = client.get_or_create_collection(
    name="knolex_research_papers",
    metadata={"hnsw:space": "cosine"},
)


def store_chunks(chunks: list[dict], filename: str) -> int:
    """Store text chunks with their original page numbers."""

    if not chunks:
        return 0

    # Create stable IDs for the chunks.
    ids = []
    documents = []
    metadatas = []

    for index, chunk in enumerate(chunks):
        text = chunk.get("text", "").strip()

        if not text:
            continue

        chunk_id = hashlib.sha256(
            f"{filename}:{index}:{text}".encode("utf-8")
        ).hexdigest()[:32]

        ids.append(chunk_id)
        documents.append(text)
        metadatas.append({
            "filename": filename,
            "page": int(chunk.get("page", 0)),
            "chunk_index": index,
        })

    if not documents:
        return 0

    # Replace existing chunks for this filename to avoid duplicates.
    existing = collection.get(
        where={"filename": filename},
        include=["metadatas"],
    )
    existing_ids = existing.get("ids", [])

    if existing_ids:
        collection.delete(ids=existing_ids)

    collection.add(
        ids=ids,
        documents=documents,
        metadatas=metadatas,
    )

    return len(documents)


def query_chunks(question: str, filename: str | None = None, top_k: int = 3) -> list[dict]:
    """Retrieve the most relevant chunks for a question."""

    question = question.strip()

    if not question:
        return []

    if collection.count() == 0:
        return []

    query_options = {
        "query_texts": [question],
        "n_results": min(top_k, collection.count()),
        "include": ["documents", "metadatas", "distances"],
    }

    if filename:
        query_options["where"] = {"filename": filename}

        matching = collection.get(
            where={"filename": filename},
            include=["metadatas"],
        )

        if not matching.get("ids"):
            return []

        query_options["n_results"] = min(
            top_k, len(matching["ids"])
        )

    results = collection.query(**query_options)

    documents = results.get("documents", [[]])[0]
    metadatas = results.get("metadatas", [[]])[0]
    distances = results.get("distances", [[]])[0]

    return [
        {
            "text": document,
            "filename": metadata.get("filename", ""),
            "page": metadata.get("page", 0),
            "distance": distance,
        }
        for document, metadata, distance in zip(
            documents, metadatas, distances
        )
    ]


def list_sources() -> list[str]:
    """Return filenames currently stored in the database."""

    results = collection.get(include=["metadatas"])

    filenames = {
        metadata.get("filename", "")
        for metadata in results.get("metadatas", [])
        if metadata.get("filename")
    }

    return sorted(filenames)


def remove_source(filename: str) -> bool:
    """Remove all stored chunks belonging to a paper."""

    existing = collection.get(
        where={"filename": filename},
        include=["metadatas"],
    )

    ids = existing.get("ids", [])

    if not ids:
        return False

    collection.delete(ids=ids)
    return True

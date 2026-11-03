
from pathlib import Path
import shutil

from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from pdf_reader import read_pdf
from chunking import create_chunks
from vector_store import (
    store_chunks,
    query_chunks,
    list_sources,
    remove_source,
)
from embeddings import generate_answer


# --------------------------------------------------
# PATHS
# --------------------------------------------------

BASE_DIR = Path(__file__).resolve().parent
PROJECT_DIR = BASE_DIR.parent
FRONTEND_DIR = PROJECT_DIR / "frontend"
UPLOAD_DIR = BASE_DIR / "uploads"

UPLOAD_DIR.mkdir(parents=True, exist_ok=True)


# --------------------------------------------------
# FASTAPI APPLICATION
# --------------------------------------------------

app = FastAPI(
    title="KNOLEX AI Research Assistant",
    description="Your AI-powered academic research workspace.",
    version="2.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


# --------------------------------------------------
# REQUEST MODELS
# --------------------------------------------------

class QuestionRequest(BaseModel):
    question: str = Field(min_length=1)
    filename: str | None = None


class PaperRequest(BaseModel):
    filename: str | None = None


class CompareRequest(BaseModel):
    filename1: str
    filename2: str


class WritingRequest(BaseModel):
    prompt: str = ""
    text: str = ""
    task: str = "improve"


class CitationRequest(BaseModel):
    text: str = ""


# --------------------------------------------------
# HEALTH CHECK
# --------------------------------------------------

@app.get("/api/health")
def health_check():
    return {
        "success": True,
        "message": "KNOLEX backend is running!",
        "version": "2.0.0",
    }


@app.get("/api")
def api_home():
    return {
        "project": "KNOLEX",
        "message": "Welcome to your AI Research Assistant.",
    }


# --------------------------------------------------
# UPLOAD AND ANALYSE PDF
# --------------------------------------------------

@app.post("/api/upload")
async def upload_pdf(file: UploadFile = File(...)):
    if not file.filename or not file.filename.lower().endswith(".pdf"):
        raise HTTPException(
            status_code=400,
            detail="Please upload a PDF file.",
        )

    filename = Path(file.filename).name
    destination = UPLOAD_DIR / filename

    try:
        with destination.open("wb") as output_file:
            shutil.copyfileobj(file.file, output_file)

        pages = read_pdf(str(destination))

        if not pages:
            raise HTTPException(
                status_code=400,
                detail="No pages could be read from this PDF.",
            )

        full_text = "\n".join(
            page["text"] for page in pages
        ).strip()

        if not full_text:
            raise HTTPException(
                status_code=400,
                detail=(
                    "No readable text was found. "
                    "This may be a scanned PDF requiring OCR."
                ),
            )

        chunks = create_chunks(pages)

        if not chunks:
            raise HTTPException(
                status_code=400,
                detail="No text chunks could be created.",
            )

        total_chunks = store_chunks(chunks, filename)

        return {
            "success": True,
            "message": "Paper uploaded and analysed successfully.",
            "filename": filename,
            "pages": len(pages),
            "characters": len(full_text),
            "total_chunks": total_chunks,
        }

    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Could not process the PDF: {exc}",
        ) from exc
    finally:
        await file.close()


# --------------------------------------------------
# LIST UPLOADED PAPERS
# --------------------------------------------------

@app.get("/api/sources")
def get_sources():
    return {
        "sources": list_sources()
    }


# --------------------------------------------------
# ASK QUESTIONS ABOUT A PAPER
# --------------------------------------------------

@app.post("/api/ask")
def ask_question(request: QuestionRequest):
    question = request.question.strip()

    if not question:
        raise HTTPException(
            status_code=400,
            detail="Please enter a question.",
        )

    try:
        chunks = query_chunks(
            question,
            filename=request.filename,
            top_k=3,
        )

        if not chunks:
            raise HTTPException(
                status_code=404,
                detail=(
                    "No matching paper content was found. "
                    "Upload a paper first, or check its filename."
                ),
            )

        context = "\n\n".join(
            f"Source: {item['filename']}, "
            f"Page: {item['page']}\n{item['text']}"
            for item in chunks
        )

        prompt = f"""
You are KNOLEX, an academic research assistant.

Answer the user's question using the provided research-paper
excerpts. Do not invent facts, quotations, or page numbers.
If the excerpts do not contain enough information, say so.
Cite supporting evidence using the filename and page number.

RESEARCH-PAPER EXCERPTS:
{context}

USER QUESTION:
{question}

Give a clear, helpful academic answer with source page numbers.
"""

        answer = generate_answer(prompt)

        sources = [
            {
                "filename": item["filename"],
                "page": item["page"],
                "text": item["text"],
            }
            for item in chunks
        ]

        return {
            "success": True,
            "answer": answer,
            "sources": sources,
        }

    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Could not answer the question: {exc}",
        ) from exc


# --------------------------------------------------
# SUMMARIZE A RESEARCH PAPER
# --------------------------------------------------

@app.post("/api/summarize")
def summarize_paper(request: PaperRequest):
    try:
        filenames = list_sources()

        if not filenames:
            raise HTTPException(
                status_code=404,
                detail="Upload a research paper before summarizing.",
            )

        filename = request.filename or filenames[-1]

        if filename not in filenames:
            raise HTTPException(
                status_code=404,
                detail=f"Paper not found: {filename}",
            )

        # Retrieve representative chunks from this paper.
        chunks = query_chunks(
            "Main research objective, methodology, findings, "
            "results, limitations and conclusions",
            filename=filename,
            top_k=8,
        )

        if not chunks:
            raise HTTPException(
                status_code=404,
                detail="No readable content was found for this paper.",
            )

        context = "\n\n".join(
            f"Page {item['page']}: {item['text']}"
            for item in chunks
        )

        prompt = f"""
Create a structured academic summary of this research paper.

Paper filename: {filename}

Use the provided excerpts only. Do not invent missing details.
Mention when information is unavailable in the excerpts.

Include:
1. Research problem and objective
2. Main methodology
3. Important findings
4. Key contributions
5. Limitations
6. Conclusion

RESEARCH-PAPER EXCERPTS:
{context}
"""

        summary = generate_answer(prompt)

        return {
            "success": True,
            "filename": filename,
            "summary": summary,
        }

    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Could not summarize the paper: {exc}",
        ) from exc


# --------------------------------------------------
# COMPARE TWO RESEARCH PAPERS
# --------------------------------------------------

@app.post("/api/compare")
def compare_papers(request: CompareRequest):
    try:
        filenames = list_sources()

        for filename in (request.filename1, request.filename2):
            if filename not in filenames:
                raise HTTPException(
                    status_code=404,
                    detail=f"Paper not found: {filename}",
                )

        paper1_chunks = query_chunks(
            "Research objective, methodology, findings, "
            "contributions and limitations",
            filename=request.filename1,
            top_k=8,
        )

        paper2_chunks = query_chunks(
            "Research objective, methodology, findings, "
            "contributions and limitations",
            filename=request.filename2,
            top_k=8,
        )

        if not paper1_chunks or not paper2_chunks:
            raise HTTPException(
                status_code=404,
                detail="Could not retrieve enough content to compare.",
            )

        paper1 = "\n\n".join(
            f"Page {item['page']}: {item['text']}"
            for item in paper1_chunks
        )

        paper2 = "\n\n".join(
            f"Page {item['page']}: {item['text']}"
            for item in paper2_chunks
        )

        prompt = f"""
Compare these two research papers using the supplied excerpts.

PAPER 1: {request.filename1}
{paper1}

PAPER 2: {request.filename2}
{paper2}

Organize the comparison under:
1. Research objectives
2. Methodologies
3. Main findings
4. Similarities
5. Differences
6. Strengths and limitations
7. Research gaps and possible future work

Do not invent details. Clearly identify which paper supports
each claim and use page numbers when available.
"""

        comparison = generate_answer(prompt)

        return {
            "success": True,
            "comparison": comparison,
            "paper1": request.filename1,
            "paper2": request.filename2,
        }

    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Could not compare papers: {exc}",
        ) from exc


# --------------------------------------------------
# ACADEMIC WRITING ASSISTANT
# --------------------------------------------------

@app.post("/api/writing")
def academic_writing(request: WritingRequest):
    text = request.text.strip()
    instruction = request.prompt.strip()
    task = request.task.strip().lower()

    if not text and not instruction:
        raise HTTPException(
            status_code=400,
            detail="Enter text or an instruction first.",
        )

    prompt = f"""
You are an academic writing assistant.

Task: {task}
User instruction: {instruction or "Improve the provided text."}

Provided text:
{text or "(No separate text provided.)"}

Help with academic clarity, grammar, structure and readability.
Preserve the original meaning. Do not invent research results,
references, quotations, or evidence.

Return the revised text and any useful brief notes.
"""

    try:
        result = generate_answer(prompt)

        return {
            "success": True,
            "result": result,
        }

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Academic writing request failed: {exc}",
        ) from exc


# --------------------------------------------------
# CITATION FINDER
# --------------------------------------------------

@app.post("/api/citations")
def find_citations(request: CitationRequest):
    text = request.text.strip()

    if not text:
        raise HTTPException(
            status_code=400,
            detail="Provide text to analyse for citations.",
        )

    prompt = f"""
Analyse the following academic text for citations and references.

TEXT:
{text}

Identify citations explicitly present in the supplied text.
Do not fabricate authors, dates, titles, DOIs or URLs.
Separate identifiable citations from incomplete references.
If no citations are present, say so.

Return a clear, structured result.
"""

    try:
        result = generate_answer(prompt)

        return {
            "success": True,
            "citations": result,
        }

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Citation analysis failed: {exc}",
        ) from exc


# --------------------------------------------------
# DELETE A PAPER
# --------------------------------------------------

@app.delete("/api/sources/{filename}")
def delete_source(filename: str):
    safe_filename = Path(filename).name

    try:
        removed_from_database = remove_source(safe_filename)
        saved_file = UPLOAD_DIR / safe_filename

        if saved_file.exists():
            saved_file.unlink()

        if not removed_from_database and not saved_file.exists():
            raise HTTPException(
                status_code=404,
                detail="Paper not found.",
            )

        return {
            "success": True,
            "message": f"Removed {safe_filename}.",
        }

    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Could not delete the paper: {exc}",
        ) from exc


# --------------------------------------------------
# SERVE THE FRONTEND
# Keep this section at the bottom.
# --------------------------------------------------

if FRONTEND_DIR.exists():
    app.mount(
        "/",
        StaticFiles(directory=str(FRONTEND_DIR), html=True),
        name="frontend",
    )

import logging
import re
from uuid import uuid4

from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from pdf_processor import extract_pages_from_pdf
from chunker import create_page_chunks
from embeddings import create_embeddings
from vector_store import create_vector_store, search_vector_store
from rag import generate_answer

from config import (
    APP_TITLE,
    APP_DESCRIPTION,
    APP_VERSION,
    UPLOAD_DIR,
    SIMILARITY_THRESHOLD,
    TOP_K,
    CHUNK_SIZE,
    CHUNK_OVERLAP,
)


# =========================================================
# LOGGING
# =========================================================

logging.basicConfig(level=logging.INFO)

logger = logging.getLogger(__name__)


# =========================================================
# CONFIGURATION
# =========================================================

MAX_UPLOAD_SIZE = 10 * 1024 * 1024
READ_BLOCK_SIZE = 1024 * 1024

SUMMARY_CANDIDATE_MULTIPLIER = 3
MAX_SUMMARY_CANDIDATES = 15

MAX_SUMMARY_CHUNKS = 12
MAX_CHUNKS_PER_PAGE = 3


# =========================================================
# APPLICATION
# =========================================================

app = FastAPI(
    title=APP_TITLE,
    description=APP_DESCRIPTION,
    version=APP_VERSION,
)


# =========================================================
# CORS
# =========================================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:5174",
        "http://127.0.0.1:5174",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# =========================================================
# UPLOAD DIRECTORY
# =========================================================

UPLOAD_DIR.mkdir(parents=True, exist_ok=True)


# =========================================================
# IN-MEMORY DOCUMENT STATE
# =========================================================

document_chunks = []
vector_index = None


# =========================================================
# REQUEST MODEL
# =========================================================

class QuestionRequest(BaseModel):
    question: str = Field(
        min_length=1,
        max_length=2000
    )


# =========================================================
# ROOT ENDPOINT
# =========================================================

@app.get("/")
def root():

    return {
        "message": "AI Document Q&A API is running"
    }


# =========================================================
# PDF UPLOAD
# =========================================================

@app.post("/upload")
async def upload_pdf(file: UploadFile = File(...)):

    global document_chunks, vector_index

    file_path = None

    try:

        if not file.filename:
            raise HTTPException(
                status_code=400,
                detail="A filename is required."
            )

        if not file.filename.lower().endswith(".pdf"):
            raise HTTPException(
                status_code=400,
                detail="Only PDF files are allowed."
            )

        # Generate a safe server-side filename.
        safe_filename = f"{uuid4().hex}.pdf"

        file_path = UPLOAD_DIR / safe_filename

        total_size = 0
        header = bytearray()

        # Save the PDF in bounded blocks.
        with file_path.open("wb") as output_file:

            while True:

                block = await file.read(READ_BLOCK_SIZE)

                if not block:
                    break

                total_size += len(block)

                if total_size > MAX_UPLOAD_SIZE:
                    raise HTTPException(
                        status_code=413,
                        detail="PDF exceeds the 10 MB upload limit."
                    )

                if len(header) < 1024:

                    remaining = 1024 - len(header)

                    header.extend(block[:remaining])

                output_file.write(block)

        if total_size == 0:
            raise HTTPException(
                status_code=400,
                detail="The uploaded file is empty."
            )

        if b"%PDF-" not in header:
            raise HTTPException(
                status_code=400,
                detail="The uploaded file does not appear to be a PDF."
            )

        # -------------------------------------------------
        # 1. EXTRACT PDF TEXT
        # -------------------------------------------------

        pages = extract_pages_from_pdf(
            str(file_path)
        )

        if not pages:
            raise HTTPException(
                status_code=400,
                detail=(
                    "No extractable text was found. "
                    "The PDF may be empty or scanned."
                )
            )

        # -------------------------------------------------
        # 2. CREATE PAGE-AWARE CHUNKS
        # -------------------------------------------------

        new_chunks = create_page_chunks(
            pages,
            chunk_size=CHUNK_SIZE,
            overlap=CHUNK_OVERLAP
        )

        if not new_chunks:
            raise HTTPException(
                status_code=400,
                detail="Could not create document chunks."
            )

        # -------------------------------------------------
        # 3. CREATE EMBEDDINGS
        # -------------------------------------------------

        chunk_texts = [
            chunk["text"]
            for chunk in new_chunks
        ]

        embeddings = create_embeddings(
            chunk_texts
        )

        if len(embeddings) != len(new_chunks):
            raise RuntimeError(
                "Embedding count does not match chunk count."
            )

        # -------------------------------------------------
        # 4. CREATE VECTOR STORE
        # -------------------------------------------------

        new_vector_index = create_vector_store(
            embeddings
        )

        # Replace the active document only after
        # successful extraction, embedding and indexing.
        document_chunks = new_chunks
        vector_index = new_vector_index

        logger.info(
            "PDF processed successfully: %s pages, %s chunks",
            len(pages),
            len(new_chunks)
        )

        return {
            "filename": file.filename,
            "message": "Document processed successfully",
            "pages": len(pages),
            "chunks": len(new_chunks)
        }

    except HTTPException:
        raise

    except Exception:

        logger.exception("PDF processing failed")

        raise HTTPException(
            status_code=500,
            detail=(
                "Document processing failed. "
                "Please try another PDF."
            )
        )

    finally:

        await file.close()

        # The PDF itself is not needed after processing.
        if file_path is not None:

            try:
                file_path.unlink(missing_ok=True)

            except OSError:

                logger.warning(
                    "Could not delete temporary upload file."
                )


# =========================================================
# QUESTION CLASSIFICATION
# =========================================================

def is_broad_question(question: str) -> bool:
    """
    Identify general document-summary questions.

    This classification uses generic question wording only.
    It does not depend on the document's subject or content.
    """

    q = question.lower().strip()

    broad_phrases = [
        "what is this document about",
        "what is the document about",
        "summarize this document",
        "summarize the document",
        "summarise this document",
        "summarise the document",
        "give me a summary",
        "document summary",
        "document overview",
        "overall summary",
        "main idea of this document",
        "key points of this document",
        "explain this document",
        "overview of the document",
        "summarize this pdf",
        "summarise this pdf",
        "give an overview",
    ]

    return any(
        phrase in q
        for phrase in broad_phrases
    )


# =========================================================
# CHUNK DEDUPLICATION
# =========================================================

def remove_duplicate_chunks(
    chunks,
    overlap_threshold=0.88
):
    """
    Remove exact duplicates and highly overlapping passages.

    The higher-ranked passage is retained.
    """

    unique_chunks = []
    seen_exact = set()

    for chunk in chunks:

        text = " ".join(
            chunk["text"].lower().split()
        )

        if not text or text in seen_exact:
            continue

        seen_exact.add(text)

        words = set(
            re.findall(r"\b\w+\b", text)
        )

        is_duplicate = False

        for existing in unique_chunks:

            existing_words = set(
                re.findall(
                    r"\b\w+\b",
                    existing["text"].lower()
                )
            )

            smaller_size = min(
                len(words),
                len(existing_words)
            )

            # Avoid removing short passages because
            # of a few commonly shared words.
            if smaller_size < 20:
                continue

            overlap = (
                len(words & existing_words)
                / smaller_size
            )

            if overlap >= overlap_threshold:

                is_duplicate = True
                break

        if not is_duplicate:
            unique_chunks.append(chunk)

    return unique_chunks


# =========================================================
# DIVERSE CHUNK SELECTION
# =========================================================

def select_diverse_chunks(
    chunks,
    max_chunks=12,
    max_chunks_per_page=3
):
    """
    Select relevant chunks from different pages.

    Only chunks that have already passed the similarity
    threshold are considered.
    """

    if not chunks:
        return []

    # Group candidates by page.
    page_groups = {}

    for chunk in chunks:

        page = chunk["page"]

        if page not in page_groups:
            page_groups[page] = []

        page_groups[page].append(chunk)

    # Sort each page's chunks by relevance.
    for page in page_groups:

        page_groups[page].sort(
            key=lambda item: item["similarity"],
            reverse=True
        )

    selected = []

    # Round-robin selection across pages.
    max_candidates = max(
        len(page_chunks)
        for page_chunks in page_groups.values()
    )

    for rank in range(max_candidates):

        if len(selected) >= max_chunks:
            break

        for page_chunks in page_groups.values():

            if len(selected) >= max_chunks:
                break

            if rank < min(
                len(page_chunks),
                max_chunks_per_page
            ):

                selected.append(
                    page_chunks[rank]
                )

    selected = remove_duplicate_chunks(selected)

    # Return results in relevance order.
    selected.sort(
        key=lambda item: item["similarity"],
        reverse=True
    )

    return selected


# =========================================================
# RETRIEVAL
# =========================================================

def retrieve_relevant_chunks(question: str):
    """
    Retrieve relevant passages for the user's question.

    Broad questions use all document chunks.
    Normal questions use FAISS similarity search.
    """

    broad_question = is_broad_question(question)

    logger.info("Broad question: %s", broad_question)

    # -------------------------------------------------
    # 1. DOCUMENT-WIDE RETRIEVAL FOR SUMMARY QUESTIONS
    # -------------------------------------------------

    if broad_question:

        logger.info(
            "Using document-wide retrieval. Total chunks: %s",
            len(document_chunks)
        )

        relevant_chunks = []

        for index, chunk in enumerate(document_chunks):

            relevant_chunks.append({
                **chunk,
                "chunk_index": index,
                "similarity": 1.0
            })

        # Remove duplicate passages.
        relevant_chunks = remove_duplicate_chunks(
            relevant_chunks
        )

        # Keep chunks in their original document order.
        relevant_chunks.sort(
            key=lambda item: (
                item["page"],
                item["chunk_index"]
            )
        )

        retrieval_debug = [
            {
                "chunk_index": chunk["chunk_index"],
                "page": chunk["page"],
                "similarity": None,
                "above_threshold": True,
                "text_preview": chunk["text"][:300]
            }
            for chunk in relevant_chunks
        ]

        logger.info(
            "Selected %s chunks for document summary",
            len(relevant_chunks)
        )

        return relevant_chunks, retrieval_debug

    # -------------------------------------------------
    # 2. NORMAL QUESTION RETRIEVAL USING FAISS
    # -------------------------------------------------

    candidate_k = min(
        TOP_K,
        len(document_chunks)
    )

    query_embedding = create_embeddings(
        [question]
    )

    similarities, indices = search_vector_store(
        vector_index,
        query_embedding,
        k=candidate_k
    )

    relevant_chunks = []
    retrieval_debug = []

    for score, chunk_index in zip(
        similarities[0],
        indices[0]
    ):

        score = float(score)
        chunk_index = int(chunk_index)

        if not (
            0 <= chunk_index < len(document_chunks)
        ):
            continue

        chunk = document_chunks[chunk_index]

        accepted = score >= SIMILARITY_THRESHOLD

        retrieval_debug.append({
            "chunk_index": chunk_index,
            "page": chunk["page"],
            "similarity": round(score, 4),
            "above_threshold": accepted,
            "text_preview": chunk["text"][:300]
        })

        logger.info(
            "Chunk %s | Page %s | Similarity %.4f | Accepted: %s",
            chunk_index,
            chunk["page"],
            score,
            accepted
        )

        if not accepted:
            continue

        relevant_chunks.append({
            **chunk,
            "chunk_index": chunk_index,
            "similarity": score
        })

    relevant_chunks = remove_duplicate_chunks(
        relevant_chunks
    )

    relevant_chunks = relevant_chunks[:TOP_K]

    logger.info(
        "Selected %s relevant chunks",
        len(relevant_chunks)
    )

    return relevant_chunks, retrieval_debug
# =========================================================
# ASK QUESTION
# =========================================================

@app.post("/ask")
def ask_question(request: QuestionRequest):

    if vector_index is None or not document_chunks:

        raise HTTPException(
            status_code=400,
            detail="Please upload a PDF first."
        )

    question = request.question.strip()

    if not question:

        raise HTTPException(
            status_code=400,
            detail="Question cannot be empty."
        )

    try:

        logger.info(
            "Received question: %s",
            question
        )

        # -------------------------------------------------
        # 1. RETRIEVE RELEVANT CHUNKS
        # -------------------------------------------------

        relevant_chunks, retrieval_debug = (
            retrieve_relevant_chunks(question)
        )

        # -------------------------------------------------
        # 2. HANDLE MISSING EVIDENCE
        # -------------------------------------------------

        if not relevant_chunks:

            return {
                "question": question,
                "answer": (
                    "I could not find enough relevant information "
                    "in the retrieved passages to answer this "
                    "question. Try rephrasing it or checking "
                    "whether the uploaded PDF contains the "
                    "required information."
                ),
                "sources": [],
                "retrieval_debug": retrieval_debug
            }

        # -------------------------------------------------
        # 3. BUILD CONTEXT WITH PAGE NUMBERS
        # -------------------------------------------------

        context_parts = []

        for chunk in relevant_chunks:

            context_parts.append(
                f"[Page {chunk['page']}]\n{chunk['text']}"
            )

        context = "\n\n".join(context_parts)

        # -------------------------------------------------
        # 4. GENERATE ANSWER
        # -------------------------------------------------

        answer = generate_answer(
            question=question,
            context=context
        )

        # -------------------------------------------------
        # 5. RETURN ANSWER AND SOURCES
        # -------------------------------------------------

        sources = [
            {
                "page": chunk["page"],
                "text": chunk["text"],
                "similarity": round(
                    chunk["similarity"],
                    4
                )
            }
            for chunk in relevant_chunks
        ]

        return {
            "question": question,
            "answer": answer,
            "sources": sources,
            "retrieval_debug": retrieval_debug
        }

    except HTTPException:
        raise

    except Exception:

        logger.exception(
            "Question processing failed"
        )

        raise HTTPException(
            status_code=500,
            detail=(
                "Failed to process your question. "
                "Please try again."
            )
        )
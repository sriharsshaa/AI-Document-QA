from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pathlib import Path
from pydantic import BaseModel

from pdf_processor import extract_pages_from_pdf
from chunker import create_page_chunks
from embeddings import create_embeddings
from vector_store import (
    create_vector_store,
    search_vector_store
)
from rag import generate_answer


app = FastAPI(
    title="AI Document Q&A API",
    description="RAG-based document question answering system",
    version="1.0.0"
)


# =========================
# CORS
# =========================

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# =========================
# CONFIGURATION
# =========================

UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)

# Minimum cosine similarity required
# for a chunk to be considered relevant.
SIMILARITY_THRESHOLD = 0.20

# Maximum number of chunks sent to the LLM.
TOP_K = 3


# =========================
# IN-MEMORY DOCUMENT STATE
# =========================

document_chunks = []
vector_index = None


# =========================
# REQUEST MODEL
# =========================

class QuestionRequest(BaseModel):
    question: str


# =========================
# ROOT ENDPOINT
# =========================

@app.get("/")
def root():
    return {
        "message": "AI Document Q&A API is running"
    }


# =========================
# PDF UPLOAD
# =========================

@app.post("/upload")
async def upload_pdf(
    file: UploadFile = File(...)
):

    global document_chunks
    global vector_index

    # Validate file type
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(
            status_code=400,
            detail="Only PDF files are allowed"
        )

    try:

        # =========================
        # SAVE UPLOADED FILE
        # =========================

        file_path = UPLOAD_DIR / file.filename

        file_content = await file.read()

        with open(file_path, "wb") as buffer:
            buffer.write(file_content)

        # =========================
        # EXTRACT TEXT
        # =========================

        pages = extract_pages_from_pdf(
            str(file_path)
        )

        if not pages:
            raise HTTPException(
                status_code=400,
                detail="Could not extract text from PDF"
            )

        # =========================
        # CREATE CHUNKS
        # =========================

        document_chunks = create_page_chunks(
            pages,
            chunk_size=500,
            overlap=100
        )

        if not document_chunks:
            raise HTTPException(
                status_code=400,
                detail="Could not create document chunks"
            )

        # =========================
        # CREATE EMBEDDINGS
        # =========================

        chunk_texts = [
            chunk["text"]
            for chunk in document_chunks
        ]

        embeddings = create_embeddings(
            chunk_texts
        )

        # =========================
        # CREATE FAISS INDEX
        # =========================

        vector_index = create_vector_store(
            embeddings
        )

        return {
            "filename": file.filename,
            "message": "Document processed successfully",
            "pages": len(pages),
            "chunks": len(document_chunks)
        }

    except HTTPException:
        raise

    except Exception as e:

        raise HTTPException(
            status_code=500,
            detail=f"Document processing failed: {str(e)}"
        )


# =========================
# ASK QUESTION
# =========================

@app.post("/ask")
def ask_question(
    request: QuestionRequest
):

    global document_chunks
    global vector_index

    # =========================
    # CHECK DOCUMENT
    # =========================

    if vector_index is None:
        raise HTTPException(
            status_code=400,
            detail="Please upload a PDF first"
        )

    # =========================
    # VALIDATE QUESTION
    # =========================

    if not request.question.strip():
        raise HTTPException(
            status_code=400,
            detail="Question cannot be empty"
        )

    try:

        # =========================
        # QUERY EXPANSION
        # =========================

        # Start with the user's original question.
        retrieval_query = request.question

        question_lower = request.question.lower()

        # Improve retrieval for regulation labels.
        if "downregulated" in question_lower:
            retrieval_query += (
                " regulation labels numerically encoded "
                "Downregulated = -1"
            )

        elif "upregulated" in question_lower:
            retrieval_query += (
                " regulation labels numerically encoded "
                "Upregulated = 1"
            )

        # Improve retrieval for mean pooling questions.
        elif "mean pooling" in question_lower:
            retrieval_query += (
                " converts variable-length representations "
                "into fixed-size vectors"
            )

        # Improve retrieval for DNABERT-2 questions.
        elif "dnabert" in question_lower:
            retrieval_query += (
                " gene DNA sequences transformer model "
                "mean pooling"
            )

        # Improve retrieval for ChemBERTa questions.
        elif "chemberta" in question_lower:
            retrieval_query += (
                " metabolite SMILES chemical structure "
                "mean pooling"
            )

        # =========================
        # CREATE QUERY EMBEDDING
        # =========================

        query_embedding = create_embeddings(
            [retrieval_query]
        )

        # =========================
        # NUMBER OF CHUNKS
        # =========================

        number_of_chunks = len(
            document_chunks
        )

        k = min(
            TOP_K,
            number_of_chunks
        )

        # =========================
        # FAISS SEARCH
        # =========================

        similarities, indices = search_vector_store(
            vector_index,
            query_embedding,
            k=k
        )

        # =========================
        # FILTER BY THRESHOLD
        # =========================

        relevant_chunks = []

        for similarity, index in zip(
            similarities[0],
            indices[0]
        ):

            # Ignore invalid FAISS indexes.
            if index < 0:
                continue

            # Ignore chunks below similarity threshold.
            if similarity < SIMILARITY_THRESHOLD:
                continue

            if index < len(document_chunks):

                chunk = document_chunks[index]

                # Store similarity internally.
                chunk_with_score = {
                    **chunk,
                    "similarity": float(similarity)
                }

                relevant_chunks.append(
                    chunk_with_score
                )

        # =========================
        # NO RELEVANT INFORMATION
        # =========================

        if not relevant_chunks:

            return {
                "question": request.question,
                "answer": (
                    "I could not find enough information "
                    "in the uploaded document to answer "
                    "this question."
                ),
                "sources": []
            }

        # =========================
        # BUILD CONTEXT
        # =========================

        context = "\n\n".join(
            chunk["text"]
            for chunk in relevant_chunks
        )

        # =========================
        # GENERATE ANSWER
        # =========================

        answer = generate_answer(
            request.question,
            context
        )

        # =========================
        # RETURN RESPONSE
        # =========================

        return {
            "question": request.question,
            "answer": answer,
            "sources": [
                {
                    "page": chunk["page"],
                    "text": chunk["text"]
                }
                for chunk in relevant_chunks
            ]
        }

    except Exception as e:

        raise HTTPException(
            status_code=500,
            detail=f"Question processing failed: {str(e)}"
        )
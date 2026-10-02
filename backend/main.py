from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pathlib import Path
from pydantic import BaseModel

from pdf_processor import extract_pages_from_pdf
from chunker import create_page_chunks
from embeddings import create_embeddings
from vector_store import create_vector_store, search_vector_store
from rag import generate_answer


app = FastAPI(
    title="AI Document Q&A API",
    description="RAG-based document question answering system",
    version="1.0.0"
)


# --------------------------------------------------
# CORS
# --------------------------------------------------

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


# --------------------------------------------------
# Upload directory
# --------------------------------------------------

UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)


# --------------------------------------------------
# In-memory document storage
# --------------------------------------------------

document_chunks = []
vector_index = None


# --------------------------------------------------
# Request model
# --------------------------------------------------

class QuestionRequest(BaseModel):
    question: str


# --------------------------------------------------
# Root endpoint
# --------------------------------------------------

@app.get("/")
def root():
    return {
        "message": "AI Document Q&A API is running"
    }


# --------------------------------------------------
# Upload PDF
# --------------------------------------------------

@app.post("/upload")
async def upload_pdf(file: UploadFile = File(...)):

    global document_chunks
    global vector_index

    # Check file type
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(
            status_code=400,
            detail="Only PDF files are allowed"
        )

    try:

        # Save PDF
        file_path = UPLOAD_DIR / file.filename

        file_content = await file.read()

        with open(file_path, "wb") as buffer:
            buffer.write(file_content)


        # Extract text page by page
        pages = extract_pages_from_pdf(
            str(file_path)
        )

        if not pages:
            raise HTTPException(
                status_code=400,
                detail="Could not extract text from PDF"
            )


        # Create page-aware chunks
        document_chunks = create_page_chunks(
            pages,
            chunk_size=500,
            overlap=100
        )


        # Extract text for embeddings
        chunk_texts = [
            chunk["text"]
            for chunk in document_chunks
        ]


        # Create embeddings
        embeddings = create_embeddings(
            chunk_texts
        )


        # Create FAISS index
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


# --------------------------------------------------
# Ask question
# --------------------------------------------------

@app.post("/ask")
def ask_question(request: QuestionRequest):

    global document_chunks
    global vector_index

    if vector_index is None:
        raise HTTPException(
            status_code=400,
            detail="Please upload a PDF first"
        )


    if not request.question.strip():
        raise HTTPException(
            status_code=400,
            detail="Question cannot be empty"
        )


    # Convert question into embedding
    query_embedding = create_embeddings(
        [request.question]
    )

    k = min(3, len(document_chunks))
    # Search FAISS
    distances, indices = search_vector_store(
        vector_index,
        query_embedding,
        k=k
    )


    # Get relevant chunks
    relevant_chunks = []

    for index in indices[0]:

        if index < len(document_chunks):

            relevant_chunks.append(
                document_chunks[index]
            )


    # Combine retrieved text
    context = "\n\n".join(
        chunk["text"]
        for chunk in relevant_chunks
    )


    # Generate answer
    answer = generate_answer(
        request.question,
        context
    )


    return {
        "question": request.question,
        "answer": answer,
        "sources": relevant_chunks
    }
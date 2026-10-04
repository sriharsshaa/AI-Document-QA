# AI Document Q&A System

An AI-powered document question-answering system using **Retrieval-Augmented Generation (RAG)**. Upload a PDF, ask questions about its content, and receive answers grounded in the uploaded document.

## ✨ Features

* 📄 Upload PDF documents
* 🔍 Extract and process document text
* ✂️ Split documents into searchable chunks
* 🧠 Generate semantic embeddings using Sentence Transformers
* ⚡ Perform similarity search using FAISS
* 🤖 Generate answers using a local Ollama LLM
* 📚 Retrieve relevant document context for each question
* 🛡️ Restrict answers to information available in the uploaded document
* 💻 Modern React-based user interface
* 🔒 Runs locally without sending documents to external AI services

## 🏗️ Architecture

```text
PDF Document
     ↓
Text Extraction
     ↓
Text Chunking
     ↓
Sentence Transformer Embeddings
     ↓
FAISS Vector Search
     ↓
Relevant Document Chunks
     ↓
Ollama LLM
     ↓
Grounded Answer
```

## 🛠️ Tech Stack

### Frontend

* React
* Vite
* CSS

### Backend

* Python
* FastAPI
* PyMuPDF

### AI / RAG

* Sentence Transformers
* FAISS
* Ollama
* Llama 3.2


## 🚀 Running the Project

### 1. Clone the repository

```bash
git clone https://github.com/YOUR_USERNAME/AI-Document-QA.git
cd AI-Document-QA
```

### 2. Backend Setup

Open a terminal and navigate to the backend:

```bash
cd backend
```

Create and activate a virtual environment:

```bash
python -m venv venv
```

Windows:

```bash
venv\Scripts\activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

Start the FastAPI server:

```bash
python -m uvicorn main:app --reload
```

The backend will run at:

```text
http://localhost:8000
```

### 3. Ollama Setup

Install Ollama and make sure the required model is available locally:

```bash
ollama pull llama3.2:3b
```

Then make sure Ollama is running before asking questions.

### 4. Frontend Setup

Open another terminal:

```bash
cd frontend
```

Install dependencies:

```bash
npm install
```

Start the React development server:

```bash
npm run dev
```

Open the URL shown by Vite, usually:

```text
http://localhost:5173
```

## 💡 How It Works

1. Upload a PDF through the React interface.
2. FastAPI receives and processes the document.
3. PyMuPDF extracts the text.
4. The extracted text is divided into smaller chunks.
5. Sentence Transformers converts the chunks into vector embeddings.
6. FAISS stores the embeddings for similarity search.
7. When a question is submitted, the question is converted into an embedding.
8. FAISS retrieves the most relevant document chunks.
9. The retrieved context is provided to the local Ollama LLM.
10. The LLM generates an answer based only on the retrieved document context.

## 🔒 Local AI

The project is designed to run locally.

Documents are processed on the local machine, and the LLM runs through Ollama rather than requiring a paid external LLM API.

## 📌 Current Limitations

* Currently processes one uploaded document at a time.
* OCR is not currently included for scanned/image-only PDFs.
* Vector data is currently maintained in memory.
* Retrieval can be further improved using similarity thresholds and advanced retrieval techniques.

## 🔮 Future Improvements

* Multi-document support
* Chat history
* Better source highlighting
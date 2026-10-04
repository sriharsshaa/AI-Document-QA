import { useEffect, useState } from "react";
import "./App.css";

function App() {
  const [file, setFile] = useState(null);
  const [question, setQuestion] = useState("");

  const [uploading, setUploading] = useState(false);
  const [uploadMessage, setUploadMessage] = useState("");

  const [asking, setAsking] = useState(false);
  const [answer, setAnswer] = useState("");
  const [sources, setSources] = useState([]);

  const [heroIndex, setHeroIndex] = useState(0);

  const heroTexts = [
    "Get answers from your documents.",
    "Understand your documents faster.",
    "Find information with AI.",
    "Search your PDFs intelligently.",
  ];

  /*
   * Change the hero text every 3 seconds.
   */
  useEffect(() => {
    const interval = setInterval(() => {
      setHeroIndex((currentIndex) => {
        return (currentIndex + 1) % heroTexts.length;
      });
    }, 3000);

    return () => clearInterval(interval);
  }, []);


  /* =========================
     FILE SELECTION
  ========================= */

  const handleFileChange = (event) => {
    const selectedFile = event.target.files[0];

    if (selectedFile) {
      setFile(selectedFile);
      setUploadMessage("");
      setAnswer("");
      setSources([]);
    }
  };


  /* =========================
     UPLOAD PDF
  ========================= */

  const handleUpload = async () => {
    if (!file) {
      return;
    }

    setUploading(true);
    setUploadMessage("");
    setAnswer("");
    setSources([]);

    const formData = new FormData();

    formData.append("file", file);

    try {
      const response = await fetch(
        "http://localhost:8000/upload",
        {
          method: "POST",
          body: formData,
        }
      );

      const data = await response.json();

      if (!response.ok) {
        throw new Error(
          data.detail || "Upload failed"
        );
      }

      setUploadMessage(
        `Document processed successfully. ${data.pages} pages, ${data.chunks} chunks.`
      );

    } catch (error) {

      setUploadMessage(
        `Error: ${error.message}`
      );

    } finally {

      setUploading(false);

    }
  };


  /* =========================
     ASK QUESTION
  ========================= */

  const handleAsk = async () => {

    if (!question.trim()) {
      return;
    }

    setAsking(true);
    setAnswer("");
    setSources([]);

    try {

      const response = await fetch(
        "http://localhost:8000/ask",
        {
          method: "POST",

          headers: {
            "Content-Type": "application/json",
          },

          body: JSON.stringify({
            question: question.trim(),
          }),
        }
      );

      const data = await response.json();

      if (!response.ok) {

        throw new Error(
          data.detail ||
          "Failed to get answer"
        );

      }

      setAnswer(data.answer);

      setSources(
        data.sources || []
      );

    } catch (error) {

      setAnswer(
        `Error: ${error.message}`
      );

    } finally {

      setAsking(false);

    }
  };


  /* =========================
     REMOVE FILE
  ========================= */

  const removeFile = () => {

    setFile(null);

    setUploadMessage("");

    setAnswer("");

    setSources("");

    setQuestion("");

  };


  /* =========================
     GROUP SOURCES
  ========================= */

  const groupedSources =
    sources.reduce(
      (groups, source) => {

        const page = source.page;

        if (!groups[page]) {
          groups[page] = [];
        }

        groups[page].push(
          source.text
        );

        return groups;

      },
      {}
    );


  return (

    <div className="app">


      {/* =========================
          HEADER
      ========================= */}

      <header className="header">

        <div className="logo">

          <div className="logo-icon">
            ✦
          </div>

          <div>

            <h1>
              DocuMind
            </h1>

            <span>
              AI Document Q&A
            </span>

          </div>

        </div>


        <div className="status">

          <span className="status-dot"></span>

          Local AI

        </div>

      </header>


      {/* =========================
          MAIN
      ========================= */}

      <main className="main">


        {/* =========================
            HERO
        ========================= */}

        <section className="hero">

          <div className="badge">
            ✨ Powered by RAG
          </div>


          <h2>

            Ask questions.

            <br />

            <span
              key={heroIndex}
              className="hero-changing-text"
            >
              {heroTexts[heroIndex]}
            </span>

          </h2>


          <p>
            Upload a PDF and use AI to understand,
            search, and ask questions about its content.
          </p>

        </section>


        {/* =========================
            WORKSPACE
        ========================= */}

        <div className="workspace">


          {/* =========================
              UPLOAD CARD
          ========================= */}

          <div className="card upload-card">


            <div className="card-header">

              <div className="card-icon">
                ↑
              </div>


              <div>

                <h3>
                  Upload Document
                </h3>

                <p>
                  Upload a PDF to start asking questions
                </p>

              </div>

            </div>


            {/* DROP ZONE */}

            <label className="drop-zone">

              <input
                type="file"
                accept=".pdf,application/pdf"
                onChange={handleFileChange}
              />


              <div className="upload-icon">
                ↑
              </div>


              <strong>

                {file
                  ? file.name
                  : "Drop your PDF here"}

              </strong>


              <span>
                or click to browse from your computer
              </span>

            </label>


            {/* SELECTED FILE */}

            {file && (

              <div className="selected-file">

                <div className="file-icon">
                  PDF
                </div>


                <div className="file-info">

                  <strong>
                    {file.name}
                  </strong>


                  <span>

                    {(
                      file.size /
                      1024 /
                      1024
                    ).toFixed(2)}

                    {" "}MB

                  </span>

                </div>


                <button
                  className="remove-btn"
                  onClick={removeFile}
                  type="button"
                >
                  ×
                </button>

              </div>

            )}


            {/* UPLOAD BUTTON */}

            <button
              className="primary-btn"
              disabled={
                !file ||
                uploading
              }
              onClick={handleUpload}
              type="button"
            >

              {uploading
                ? "Processing..."
                : "Upload & Process"}


              <span>

                {uploading
                  ? "..."
                  : "→"}

              </span>

            </button>


            {/* UPLOAD MESSAGE */}

            {uploadMessage && (

              <div className="upload-message">

                {uploadMessage}

              </div>

            )}

          </div>


          {/* =========================
              QUESTION CARD
          ========================= */}

          <div className="card question-card">


            <div className="card-header">

              <div className="card-icon">
                ✦
              </div>


              <div>

                <h3>
                  Ask Your Document
                </h3>


                <p>
                  Ask anything about the uploaded content
                </p>

              </div>

            </div>


            {/* QUESTION BOX */}

            <div className="question-box">


              <textarea

                placeholder="What would you like to know?"

                value={question}

                onChange={(event) =>
                  setQuestion(
                    event.target.value
                  )
                }

              />


              <div className="question-footer">


                <span>
                  {question.length} characters
                </span>


                <button

                  className="ask-btn"

                  disabled={
                    !question.trim() ||
                    asking
                  }

                  onClick={handleAsk}

                  type="button"

                >

                  {asking
                    ? "Thinking..."
                    : "Ask AI"}


                  <span>

                    {asking
                      ? "..."
                      : "↗"}

                  </span>

                </button>


              </div>

            </div>


            {/* SUGGESTIONS */}

            <div className="suggestions">


              <span>
                Try asking:
              </span>


              <button
                type="button"
                onClick={() =>
                  setQuestion(
                    "What is this document about?"
                  )
                }
              >
                What is this document about?
              </button>


              <button
                type="button"
                onClick={() =>
                  setQuestion(
                    "Summarize the key points"
                  )
                }
              >
                Summarize the key points
              </button>


            </div>

          </div>

        </div>


        {/* =========================
            ANSWER SECTION
        ========================= */}

        {(answer || asking) && (

          <section className="answer-section">


            <div className="answer-header">


              <div className="answer-icon">
                ✦
              </div>


              <div>

                <h3>
                  AI Answer
                </h3>


                <span>
                  Generated from your uploaded document
                </span>

              </div>


            </div>


            {/* ANSWER */}

            <div className="answer-content">


              {asking ? (
                  <div className="thinking">
                    <span className="thinking-spinner"></span>
                    <span>
                      Searching your document and generating an answer...
                    </span>
                  </div>
                ) : (
                  <p>
                    {answer}
                  </p>
                )}

            </div>


            {/* SOURCES */}

            {!asking &&
              sources.length > 0 && (

                <div className="sources">


                  <h4>
                    Sources
                  </h4>


                  {Object.values(
                    groupedSources
                  ).map(
                    (texts, index) => (

                      <div
                        className="source-page-group"
                        key={index}
                      >


                        {texts.map(
                          (text, textIndex) => (

                            <div
                              className="source-text"
                              key={textIndex}
                            >

                              • {text}

                            </div>

                          )
                        )}

                      </div>

                    )
                  )}

                </div>

              )}

          </section>

        )}


        {/* =========================
            FEATURES
        ========================= */}

        <section className="features">


          <div className="feature">

            <div>
              📄
            </div>

            <strong>
              Document-aware
            </strong>

            <span>
              Answers based on your uploaded PDF
            </span>

          </div>


          <div className="feature">

            <div>
              ⚡
            </div>

            <strong>
              Semantic Search
            </strong>

            <span>
              Finds relevant information using embeddings
            </span>

          </div>


          <div className="feature">

            <div>
              🔒
            </div>

            <strong>
              Runs Locally
            </strong>

            <span>
              Your documents stay on your machine
            </span>

          </div>


        </section>


      </main>


      {/* =========================
          FOOTER
      ========================= */}

      <footer>

        <span>
          DocuMind
        </span>

        <span>
          •
        </span>

        <span>
          Built with React + FastAPI + RAG + Ollama
        </span>

      </footer>


    </div>

  );
}

export default App;

import { useEffect, useRef, useState } from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import "./App.css";

function normalizeMarkdown(text = "") {
  return text.replace(/\\([*_`])/g, "$1");
}

function App() {
  const [file, setFile] = useState(null);
  const [documentUploaded, setDocumentUploaded] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [asking, setAsking] = useState(false);
  const [uploadMessage, setUploadMessage] = useState("");
  const [question, setQuestion] = useState("");
  const [messages, setMessages] = useState([]);

  const fileInputRef = useRef(null);
  const messagesEndRef = useRef(null);
  const textareaRef = useRef(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({
      behavior: "smooth",
    });
  }, [messages, asking]);

  const handleFileChange = (event) => {
    const selectedFile = event.target.files?.[0];

    if (!selectedFile) return;

    if (
      selectedFile.type !== "application/pdf" &&
      !selectedFile.name.toLowerCase().endsWith(".pdf")
    ) {
      setUploadMessage("Please select a PDF file.");
      return;
    }

    setFile(selectedFile);
    setDocumentUploaded(false);
    setUploadMessage("");
    setMessages([]);
  };

  const handleUpload = async () => {
    if (!file || uploading || asking) return;

    setUploading(true);
    setUploadMessage("");

    const formData = new FormData();
    formData.append("file", file);

    try {
      const response = await fetch("http://localhost:8000/upload", {
        method: "POST",
        body: formData,
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.detail || "Upload failed.");
      }

      setDocumentUploaded(true);
      setMessages([
        {
          id: Date.now(),
          role: "assistant",
          content: `Your document **${file.name}** is ready! I've processed ${data.pages} pages and created ${data.chunks} searchable chunks. What would you like to know about it?`,
          sources: [],
        },
      ]);

      setUploadMessage("Document processed successfully.");
    } catch (error) {
      setDocumentUploaded(false);
      setUploadMessage(`Error: ${error.message}`);
    } finally {
      setUploading(false);
    }
  };

  const handleAsk = async (submittedQuestion = question) => {
    const trimmedQuestion = submittedQuestion.trim();

    if (
      !documentUploaded ||
      !trimmedQuestion ||
      asking ||
      uploading
    ) {
      return;
    }

    const userMessage = {
      id: Date.now(),
      role: "user",
      content: trimmedQuestion,
    };

    setMessages((previous) => [...previous, userMessage]);
    setQuestion("");
    setAsking(true);

    try {
      const response = await fetch("http://localhost:8000/ask", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          question: trimmedQuestion,
        }),
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.detail || "Failed to get an answer.");
      }

      setMessages((previous) => [
        ...previous,
        {
          id: Date.now() + 1,
          role: "assistant",
          content:
            typeof data.answer === "string"
              ? data.answer
              : "The AI returned an invalid answer.",
          sources: Array.isArray(data.sources) ? data.sources : [],
        },
      ]);
    } catch (error) {
      setMessages((previous) => [
        ...previous,
        {
          id: Date.now() + 1,
          role: "assistant",
          content: `Sorry, something went wrong: ${error.message}`,
          sources: [],
          isError: true,
        },
      ]);
    } finally {
      setAsking(false);
      textareaRef.current?.focus();
    }
  };

  const startNewChat = () => {
    if (uploading || asking) return;

    setMessages([]);
    setQuestion("");
    setUploadMessage("");
    setFile(null);
    setDocumentUploaded(false);

    if (fileInputRef.current) {
      fileInputRef.current.value = "";
    }
  };

  const handleSubmit = (event) => {
    event.preventDefault();
    handleAsk();
  };

  const suggestions = [
    "What is this document about?",
    "Summarize the key points",
    "Explain the main methodology",
    "What are the important findings?",
  ];

  return (
    <div className="app-shell">
      {/* SIDEBAR */}
      <aside className="sidebar">
        <div className="sidebar-brand">
          <div className="brand-icon">✦</div>
          <div>
            <h1>DocuMind</h1>
            <span>AI Document Assistant</span>
          </div>
        </div>

        <button
          className="new-chat-btn"
          onClick={startNewChat}
          disabled={uploading || asking}
          type="button"
        >
          <span>＋</span> New chat
        </button>

        <div className="sidebar-section">
          <span className="sidebar-label">YOUR DOCUMENT</span>

          <div className="document-panel">
            <div className="document-icon">PDF</div>
            <div className="document-details">
              <strong>
                {file ? file.name : "No document uploaded"}
              </strong>
              <span>
                {documentUploaded
                  ? "Ready to chat"
                  : file
                    ? "Waiting for upload"
                    : "Upload a PDF to begin"}
              </span>
            </div>
          </div>

          <label className="sidebar-upload-btn">
            <span>＋</span> Choose PDF
            <input
              ref={fileInputRef}
              type="file"
              accept=".pdf,application/pdf"
              onChange={handleFileChange}
              disabled={uploading || asking}
            />
          </label>

          {file && !documentUploaded && (
            <button
              className="process-btn"
              onClick={handleUpload}
              disabled={uploading || asking}
              type="button"
            >
              {uploading ? "Processing document..." : "Upload & Process"}
            </button>
          )}

          {uploadMessage && (
            <p
              className={
                uploadMessage.startsWith("Error")
                  ? "upload-status error"
                  : "upload-status"
              }
              role="status"
            >
              {uploadMessage}
            </p>
          )}
        </div>

        <div className="sidebar-bottom">
          <div className="local-status">
            <span className="status-dot" />
            Local AI · Ollama
          </div>
          <span className="sidebar-version">DocuMind v1.0</span>
        </div>
      </aside>

      {/* MAIN CHAT AREA */}
      <main className="chat-main">
        <header className="chat-header">
          <div>
            <h2>Document Chat</h2>
            <p>
              {documentUploaded
                ? `Chatting with ${file?.name}`
                : "Upload a document to start a conversation"}
            </p>
          </div>

          <div className="header-status">
            <span className="status-dot" />
            Local AI
          </div>
        </header>

        <section className="chat-content">
          {!documentUploaded && messages.length === 0 ? (
            <div className="welcome-screen">
              <div className="welcome-icon">✦</div>

              <h2>What can I help you understand?</h2>

              <p>
                Upload a PDF and start a conversation.
                Ask questions, explore ideas, and understand
                your documents with AI.
              </p>

              <button
                className="welcome-upload-btn"
                onClick={() => fileInputRef.current?.click()}
                type="button"
                disabled={uploading || asking}
              >
                <span>↑</span> Upload a PDF
              </button>

              <div className="welcome-features">
                <div>
                  <span>📄</span>
                  <strong>Document Q&A</strong>
                  <small>Get answers from your PDF</small>
                </div>
                <div>
                  <span>🔎</span>
                  <strong>Smart Search</strong>
                  <small>Find relevant information</small>
                </div>
                <div>
                  <span>🔒</span>
                  <strong>Local AI</strong>
                  <small>Runs on your machine</small>
                </div>
              </div>
            </div>
          ) : (
            <div className="messages-container">
              {messages.map((message) => (
                <div
                  className={`message-row ${message.role}`}
                  key={message.id}
                >
                  <div className="message-avatar">
                    {message.role === "assistant" ? "✦" : "You"}
                  </div>

                  <div className="message-body">
                    <span className="message-author">
                      {message.role === "assistant" ? "DocuMind" : "You"}
                    </span>

                    <div
                      className={`message-bubble ${
                        message.isError ? "message-error" : ""
                      }`}
                    >
                      <div className="markdown-content">
                        <ReactMarkdown remarkPlugins={[remarkGfm]}>
                          {normalizeMarkdown(message.content)}
                        </ReactMarkdown>
                      </div>
                    </div>

                    {message.role === "assistant" &&
                      message.sources?.length > 0 && (
                        <details className="message-sources">
                          <summary>
                            📄 View sources ({message.sources.length})
                          </summary>

                          {message.sources.map((source, index) => (
                            <div
                              className="source-item"
                              key={`${message.id}-${index}`}
                            >
                              <strong>
                                Page {source.page ?? "Unknown"}
                              </strong>
                              <p>{source.text}</p>
                            </div>
                          ))}
                        </details>
                      )}
                  </div>
                </div>
              ))}

              {asking && (
                <div className="message-row assistant">
                  <div className="message-avatar">✦</div>
                  <div className="message-body">
                    <span className="message-author">DocuMind</span>
                    <div className="thinking-bubble">
                      <span className="thinking-dot" />
                      <span className="thinking-dot" />
                      <span className="thinking-dot" />
                      <span>Thinking...</span>
                    </div>
                  </div>
                </div>
              )}

              <div ref={messagesEndRef} />
            </div>
          )}
        </section>

        {/* CHAT INPUT */}
        <footer className="chat-footer">
          {documentUploaded && messages.length <= 1 && (
            <div className="suggestion-list">
              {suggestions.map((suggestion) => (
                <button
                  key={suggestion}
                  type="button"
                  disabled={asking || uploading}
                  onClick={() => handleAsk(suggestion)}
                >
                  {suggestion}
                </button>
              ))}
            </div>
          )}

          <form className="chat-input-box" onSubmit={handleSubmit}>
            <textarea
              ref={textareaRef}
              placeholder={
                documentUploaded
                  ? "Ask anything about your document..."
                  : "Upload a PDF to start chatting..."
              }
              value={question}
              disabled={!documentUploaded || asking || uploading}
              onChange={(event) => setQuestion(event.target.value)}
              onKeyDown={(event) => {
                if (
                  event.key === "Enter" &&
                  !event.shiftKey &&
                  !event.nativeEvent.isComposing
                ) {
                  event.preventDefault();
                  handleSubmit(event);
                }
              }}
              rows={1}
            />

            <div className="input-bottom">
              <span>Enter to send · Shift + Enter for a new line</span>

              <button
                type="submit"
                disabled={
                  !documentUploaded ||
                  !question.trim() ||
                  asking ||
                  uploading
                }
                aria-label="Send message"
              >
                ↑
              </button>
            </div>
          </form>

          <p className="disclaimer">
            DocuMind can make mistakes. Verify important information
            with your original document.
          </p>
        </footer>
      </main>
    </div>
  );
}

export default App;

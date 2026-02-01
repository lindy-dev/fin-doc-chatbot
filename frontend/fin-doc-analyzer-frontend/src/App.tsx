import { useEffect, useMemo, useRef, useState } from 'react'
import './App.css'

type DocumentItem = {
  id: string
  filename: string
  uploadedAt?: string
}

type ChatMessage = {
  role: 'user' | 'assistant'
  content: string
}

const API_BASE = import.meta.env.VITE_API_BASE ?? 'http://localhost:8000/api'

function App() {
  const fileInputRef = useRef<HTMLInputElement | null>(null)
  const [documents, setDocuments] = useState<DocumentItem[]>([])
  const [selectedDoc, setSelectedDoc] = useState<string | null>(null)
  const [prompt, setPrompt] = useState('')
  const [chat, setChat] = useState<ChatMessage[]>([])
  const [uploading, setUploading] = useState(false)
  const [status, setStatus] = useState<string>('')
  const token = useMemo(() => localStorage.getItem('auth_token') ?? '', [])

  useEffect(() => {
    // Placeholder auth token for now; replace with real auth flow
    if (!token) {
      localStorage.setItem('auth_token', 'dev-token')
    }
  }, [token])

  const fetchDocuments = async () => {
    try {
      const res = await fetch(`${API_BASE}/documents`, {
        headers: { Authorization: `Bearer ${localStorage.getItem('auth_token')}` },
      })
      const data = await res.json()
      setDocuments((data ?? []).map((d: string) => ({ id: d, filename: d })))
    } catch (err) {
      console.error(err)
      setStatus('Failed to load documents')
    }
  }

  useEffect(() => {
    fetchDocuments()
  }, [])

  const handleUpload = async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault()
    const file = fileInputRef.current?.files?.[0]
    if (!file) return
    const formData = new FormData()
    formData.append('file', file)
    setUploading(true)
    setStatus('Uploading...')
    try {
      const res = await fetch(`${API_BASE}/documents/upload`, {
        method: 'POST',
        headers: {
          Authorization: `Bearer ${localStorage.getItem('auth_token')}`,
        },
        body: formData,
      })
      const data = await res.json()
      setStatus(`Uploaded ${data.filename}`)
      setDocuments((prev) => [{ id: data.stored_as ?? data.filename, filename: data.filename }, ...prev])
      setSelectedDoc(data.stored_as ?? data.filename)
      if (fileInputRef.current) {
        fileInputRef.current.value = ''
      }
    } catch (err) {
      console.error(err)
      setStatus('Upload failed')
    } finally {
      setUploading(false)
    }
  }

  const handleChatSend = async () => {
    if (!prompt || !selectedDoc) return
    const userMessage: ChatMessage = { role: 'user', content: prompt }
    setChat((prev) => [...prev, userMessage])
    setPrompt('')
    try {
      const res = await fetch(`${API_BASE}/chat`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${localStorage.getItem('auth_token')}`,
        },
        body: JSON.stringify({ prompt: userMessage.content, document_id: selectedDoc }),
      })
      const data = await res.json()
      const assistantMessage: ChatMessage = { role: 'assistant', content: data.reply ?? 'No reply' }
      setChat((prev) => [...prev, assistantMessage])
    } catch (err) {
      console.error(err)
      setStatus('Chat failed')
    }
  }

  return (
    <div className="page">
      <header className="topbar">
        <div>
          <h1>Financial Document Analyzer</h1>
          <p className="muted">Upload financial PDFs, then chat to extract insights.</p>
        </div>
        <div className="badge">MongoDB · FastAPI · React</div>
      </header>

      <section className="grid">
        <div className="card">
          <h2>Upload Document</h2>
          <p className="muted">PDF, DOCX, XLSX supported by backend processing.</p>
          <form onSubmit={handleUpload} className="upload-form">
            <input ref={fileInputRef} type="file" name="file" accept=".pdf,.docx,.xlsx" />
            <button type="submit" disabled={uploading}>
              {uploading ? 'Uploading...' : 'Upload'}
            </button>
          </form>
          {status && <p className="status">{status}</p>}
        </div>

        <div className="card">
          <div className="card-header">
            <h2>Documents</h2>
            <button onClick={fetchDocuments} className="ghost">Refresh</button>
          </div>
          <div className="doc-list">
            {documents.length === 0 && <p className="muted">No documents yet.</p>}
            {documents.map((doc) => (
              <button
                key={doc.id}
                className={`doc-item ${selectedDoc === doc.id ? 'active' : ''}`}
                onClick={() => setSelectedDoc(doc.id)}
              >
                <span>{doc.filename}</span>
                {doc.uploadedAt && <small>{doc.uploadedAt}</small>}
              </button>
            ))}
          </div>
        </div>
      </section>

      <section className="card chat">
        <div className="card-header">
          <div>
            <h2>Chat</h2>
            <p className="muted">Ask about figures, risks, and insights. Select a document first.</p>
          </div>
          {selectedDoc && <span className="pill">Doc selected</span>}
        </div>
        <div className="chat-window">
          {chat.length === 0 && <p className="muted">No messages yet.</p>}
          {chat.map((msg, idx) => (
            <div key={idx} className={`chat-row ${msg.role}`}>
              <span className="chat-role">{msg.role === 'user' ? 'You' : 'Assistant'}</span>
              <p>{msg.content}</p>
            </div>
          ))}
        </div>
        <div className="chat-input">
          <input
            type="text"
            value={prompt}
            onChange={(e) => setPrompt(e.target.value)}
            placeholder={selectedDoc ? 'Ask a question about the document' : 'Select a document to start'}
            disabled={!selectedDoc}
          />
          <button onClick={handleChatSend} disabled={!prompt || !selectedDoc}>
            Send
          </button>
        </div>
      </section>
    </div>
  )
}

export default App

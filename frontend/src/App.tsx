import { useEffect, useMemo, useRef, useState } from 'react'
import './App.css'

type ChatRole = 'user' | 'assistant' | 'system'

type ChatMessage = {
  id: string
  role: ChatRole
  content: string
  createdAt: string
}

type SseEvent = {
  type: 'status' | 'chunk' | 'complete'
  content: string
  metadata?: Record<string, unknown>
  conversation_id?: string
}

type HistoryMessage = {
  role: ChatRole
  content: string
  created_at: string
}

type HistoryResponse = {
  conversation_id: string
  messages: HistoryMessage[]
}

const API_BASE_URL = 'http://localhost:8000'
const SESSION_STORAGE_KEY = 'fin_doc_session_id'

const createMessage = (role: ChatRole, content: string): ChatMessage => ({
  id: crypto.randomUUID(),
  role,
  content,
  createdAt: new Date().toISOString(),
})

function App() {
  const [messages, setMessages] = useState<ChatMessage[]>([])
  const [input, setInput] = useState('')
  const [status, setStatus] = useState<string | null>(null)
  const [isStreaming, setIsStreaming] = useState(false)
  const [conversationId, setConversationId] = useState<string | null>(null)
  const [sessionId, setSessionId] = useState<string>('')
  const messagesEndRef = useRef<HTMLDivElement | null>(null)
  const streamingAssistantId = useRef<string | null>(null)

  const isSendDisabled = useMemo(
    () => isStreaming || input.trim().length === 0,
    [isStreaming, input]
  )

  useEffect(() => {
    const existing = localStorage.getItem(SESSION_STORAGE_KEY)
    if (existing) {
      setSessionId(existing)
      return
    }
    const generated = crypto.randomUUID()
    localStorage.setItem(SESSION_STORAGE_KEY, generated)
    setSessionId(generated)
  }, [])

  useEffect(() => {
    if (!sessionId) return

    const fetchHistory = async () => {
      try {
        const response = await fetch(
          `${API_BASE_URL}/chat/history/${sessionId}`
        )
        if (!response.ok) return
        const payload = (await response.json()) as HistoryResponse
        if (!payload?.messages) return
        const hydrated = payload.messages.map((message) => ({
          id: crypto.randomUUID(),
          role: message.role,
          content: message.content,
          createdAt: message.created_at,
        }))
        setMessages(hydrated)
        setConversationId(payload.conversation_id)
      } catch (error) {
        console.error('Failed to load chat history', error)
      }
    }

    fetchHistory()
  }, [sessionId])

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  const updateStreamingMessage = (content: string) => {
    setMessages((prev) =>
      prev.map((message) =>
        message.id === streamingAssistantId.current
          ? { ...message, content }
          : message
      )
    )
  }

  const appendStreamingChunk = (chunk: string) => {
    setMessages((prev) =>
      prev.map((message) =>
        message.id === streamingAssistantId.current
          ? { ...message, content: message.content + chunk }
          : message
      )
    )
  }

  const handleSseEvent = (event: SseEvent) => {
    if (event.type === 'status') {
      setStatus(event.content)
      return
    }

    if (event.type === 'chunk') {
      appendStreamingChunk(event.content)
      return
    }

    if (event.type === 'complete') {
      updateStreamingMessage(event.content)
      setStatus(null)
      setIsStreaming(false)
      streamingAssistantId.current = null
      if (event.conversation_id) {
        setConversationId(event.conversation_id)
      }
    }
  }

  const parseSseLine = (line: string) => {
    const trimmed = line.trim()
    if (!trimmed.startsWith('data:')) return
    const payload = trimmed.replace(/^data:\s*/, '')
    if (!payload) return
    try {
      const data = JSON.parse(payload) as SseEvent
      handleSseEvent(data)
    } catch (error) {
      console.error('Failed to parse SSE chunk', error)
    }
  }

  const streamChat = async (message: string) => {
    setIsStreaming(true)
    setStatus('sending')

    const assistantMessageId = crypto.randomUUID()
    streamingAssistantId.current = assistantMessageId

    setMessages((prev) => [
      ...prev,
      createMessage('user', message),
      {
        id: assistantMessageId,
        role: 'assistant',
        content: '',
        createdAt: new Date().toISOString(),
      },
    ])

    try {
      const response = await fetch(`${API_BASE_URL}/chat/stream`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ session_id: sessionId, message }),
      })

      if (!response.ok || !response.body) {
        throw new Error('Streaming request failed')
      }

      const reader = response.body.getReader()
      const decoder = new TextDecoder('utf-8')
      let buffer = ''

      while (true) {
        const { value, done } = await reader.read()
        if (done) break
        buffer += decoder.decode(value, { stream: true })
        const lines = buffer.split('\n')
        buffer = lines.pop() ?? ''
        lines.forEach(parseSseLine)
      }
    } catch (error) {
      console.error('Streaming failed', error)
      setStatus('error')
      setIsStreaming(false)
      streamingAssistantId.current = null
    }
  }

  const handleSubmit = async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault()
    if (!input.trim()) return
    const message = input.trim()
    setInput('')
    await streamChat(message)
  }

  const handleDeleteHistory = async () => {
    if (!conversationId) return
    try {
      const response = await fetch(
        `${API_BASE_URL}/chat/${conversationId}`,
        { method: 'DELETE' }
      )
      if (!response.ok) return
      setMessages([])
      setConversationId(null)
      setStatus(null)
    } catch (error) {
      console.error('Failed to delete history', error)
    }
  }

  return (
    <div className="app">
      <div className="app__left" />
      <div className="app__right">
        <header className="chat-header">
          <div>
            <h1>Financial Document Chat</h1>
            {status && <p className="chat-status">Status: {status}</p>}
          </div>
          <button
            className="ghost"
            onClick={handleDeleteHistory}
            disabled={!conversationId || isStreaming}
          >
            Delete history
          </button>
        </header>

        <div className="chat-messages">
          {messages.length === 0 && (
            <div className="chat-empty">
              Ask a question about a financial document to get started.
            </div>
          )}
          {messages.map((message) => (
            <div
              key={message.id}
              className={`chat-message chat-message--${message.role}`}
            >
              <div className="chat-bubble">
                <div className="chat-role">{message.role}</div>
                <div className="chat-content">{message.content}</div>
              </div>
            </div>
          ))}
          <div ref={messagesEndRef} />
        </div>

        <form className="chat-input" onSubmit={handleSubmit}>
          <textarea
            placeholder="Ask about Q2 revenue trends..."
            value={input}
            onChange={(event) => setInput(event.target.value)}
            rows={3}
            disabled={isStreaming}
          />
          <button type="submit" disabled={isSendDisabled}>
            {isStreaming ? 'Streaming...' : 'Send'}
          </button>
        </form>
      </div>
    </div>
  )
}

export default App

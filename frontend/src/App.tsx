import { useEffect, useMemo, useRef, useState } from 'react'

type ChatRole = 'user' | 'assistant' | 'system'

type ChatMessage = {
  id: string
  role: ChatRole
  content: string
  createdAt: string
  thinkingLog?: string
  isThinkingOpen?: boolean
}

type SseEvent = {
  type: 'status' | 'progress' | 'chunk' | 'complete'
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

const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8000'
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

  const appendThinkingLog = (line: string) => {
    setMessages((prev) =>
      prev.map((message) =>
        message.id === streamingAssistantId.current
          ? {
              ...message,
              thinkingLog: `${message.thinkingLog ?? ''}${line}\n`,
            }
          : message
      )
    )
  }

  const handleSseEvent = (event: SseEvent) => {
    if (event.type === 'status') {
      setStatus(event.content)
      return
    }

    if (event.type === 'progress') {
      const agent =
        typeof event.metadata?.agent === 'string' ? event.metadata.agent : null
      const task =
        typeof event.metadata?.task === 'string' ? event.metadata.task : null
      const step =
        typeof event.metadata?.step === 'string' ? event.metadata.step : null
      const prefix = [agent, task, step].filter(Boolean).join(' • ')
      const line = prefix ? `${prefix}: ${event.content}` : event.content
      appendThinkingLog(line)
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
      const conversationIdFromMeta = event.metadata?.conversation_id
      if (typeof conversationIdFromMeta === 'string') {
        setConversationId(conversationIdFromMeta)
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
        thinkingLog: '',
        isThinkingOpen: false,
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
    <div className="grid min-h-screen grid-cols-1 bg-neutral-950 text-slate-100 lg:grid-cols-[1fr_420px]">
      <div className="hidden bg-black lg:block" />
      <div className="flex min-h-screen flex-col border-l border-white/10 bg-slate-900 lg:h-screen">
        <header className="flex items-center justify-between gap-4 border-b border-white/10 px-7 pb-4 pt-6">
          <div>
            <h1 className="text-lg font-semibold">Financial Document Chat</h1>
            {status && (
              <p className="mt-1 text-xs text-sky-300">Status: {status}</p>
            )}
          </div>
          <button
            className="rounded-full border border-white/20 bg-transparent px-4 py-1.5 text-sm text-slate-200 disabled:cursor-not-allowed disabled:opacity-40"
            onClick={handleDeleteHistory}
            disabled={!conversationId || isStreaming}
          >
            Delete history
          </button>
        </header>

        <div className="flex-1 overflow-y-auto px-7 py-6">
          {messages.length === 0 && (
            <div className="mt-8 text-center text-sm text-slate-400">
              Ask a question about a financial document to get started.
            </div>
          )}
          <div className="flex flex-col gap-4">
            {messages.map((message) => (
              <div
                key={message.id}
                className={`flex ${
                  message.role === 'user' ? 'justify-end' : 'justify-start'
                }`}
              >
                <div
                  className={`max-w-[85%] rounded-2xl border border-white/10 bg-white/10 px-4 py-3 ${
                    message.role === 'user' ? 'border-blue-600 bg-blue-600' : ''
                  }`}
                >
                  <div className="mb-1 text-[0.65rem] uppercase tracking-[0.2em] text-white/70">
                    {message.role}
                  </div>
                  <div className="whitespace-pre-wrap text-sm leading-relaxed">
                    {message.content}
                  </div>
                  {message.role === 'assistant' && message.thinkingLog && (
                    <button
                      type="button"
                      className="mt-3 inline-flex items-center rounded-full border border-white/20 bg-slate-950/50 px-3 py-1 text-[0.7rem] text-slate-200"
                      onClick={() =>
                        setMessages((prev) =>
                          prev.map((entry) =>
                            entry.id === message.id
                              ? {
                                  ...entry,
                                  isThinkingOpen: !entry.isThinkingOpen,
                                }
                              : entry
                          )
                        )
                      }
                    >
                      {message.isThinkingOpen
                        ? 'Hide thinking'
                        : 'Show thinking'}
                    </button>
                  )}
                  {message.role === 'assistant' && message.isThinkingOpen && (
                    <pre className="mt-3 max-h-52 overflow-y-auto whitespace-pre-wrap rounded-xl border border-white/10 bg-slate-950/80 p-3 font-mono text-[0.7rem] text-indigo-200">
                      {message.thinkingLog || 'No SSE output captured.'}
                    </pre>
                  )}
                </div>
              </div>
            ))}
          </div>
          <div ref={messagesEndRef} />
        </div>

        <form
          className="grid grid-cols-1 gap-3 border-t border-white/10 px-7 py-6 sm:grid-cols-[1fr_auto]"
          onSubmit={handleSubmit}
        >
          <textarea
            className="w-full resize-none rounded-xl border border-white/20 bg-slate-950 px-3 py-2 text-sm text-slate-100 placeholder:text-slate-500 focus:outline-none focus:ring-2 focus:ring-sky-500/50 disabled:opacity-70"
            placeholder="Ask about Q2 revenue trends..."
            value={input}
            onChange={(event) => setInput(event.target.value)}
            rows={3}
            disabled={isStreaming}
          />
          <button
            className="self-end rounded-full bg-emerald-400 px-5 py-2 text-sm font-semibold text-slate-950 disabled:cursor-not-allowed disabled:opacity-60"
            type="submit"
            disabled={isSendDisabled}
          >
            {isStreaming ? 'Streaming...' : 'Send'}
          </button>
        </form>
      </div>
    </div>
  )
}

export default App

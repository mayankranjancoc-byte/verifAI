import { useState, useRef, useEffect } from 'react'
import InputBar from './components/InputBar'
import ChatMessage from './components/ChatMessage'
import Welcome from './components/Welcome'

const API_URL = '/api/analyze'

export default function App() {
  const [messages, setMessages] = useState([])
  const [loading, setLoading] = useState(false)
  const chatEndRef = useRef(null)

  const scrollToBottom = () => {
    chatEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  useEffect(() => {
    scrollToBottom()
  }, [messages, loading])

  const handleSend = async (input, file) => {
    if (!input.trim() && !file) return

    // Add user message
    const userMsg = {
      id: Date.now(),
      role: 'user',
      content: input,
      file: file ? { name: file.name, type: file.type } : null,
      timestamp: new Date()
    }
    setMessages(prev => [...prev, userMsg])
    setLoading(true)

    try {
      const formData = new FormData()
      formData.append('content', input)
      if (file) {
        formData.append('file', file)
      }

      const res = await fetch(API_URL, {
        method: 'POST',
        body: formData
      })

      if (!res.ok) throw new Error(`Server error: ${res.status}`)

      const data = await res.json()

      const aiMsg = {
        id: Date.now() + 1,
        role: 'ai',
        data,
        timestamp: new Date()
      }
      setMessages(prev => [...prev, aiMsg])
    } catch (err) {
      console.error('Analysis failed:', err)
      const errorMsg = {
        id: Date.now() + 1,
        role: 'ai',
        data: {
          verdict: 'ERROR',
          reality_score: 0,
          claims: [],
          key_insights: [{ icon: 'error', text: `Analysis failed: ${err.message}. Make sure the backend is running on port 8000.` }],
          trust_trail: [],
          emotion_analysis: { intensity: 0, label: '' },
          humor: { joke: '', explanation: '' },
          sources: []
        },
        timestamp: new Date()
      }
      setMessages(prev => [...prev, errorMsg])
    } finally {
      setLoading(false)
    }
  }

  const handleReanalyze = (originalContent) => {
    handleSend(originalContent)
  }

  const handleChipClick = (text) => {
    handleSend(text)
  }

  return (
    <div className="app">
      <header className="header">
        <div className="header__brand">
          <button className="icon-btn">
            <span className="material-symbols-outlined">menu</span>
          </button>
          <h1 className="header__logo">VerifAI</h1>
        </div>
        <div className="header__actions">
          <button className="icon-btn">
            <span className="material-symbols-outlined">history</span>
          </button>
          <button className="icon-btn">
            <span className="material-symbols-outlined">settings</span>
          </button>
        </div>
      </header>

      <main className="chat-area">
        {messages.length === 0 && !loading ? (
          <Welcome onChipClick={handleChipClick} />
        ) : (
          <>
            {messages.map(msg => (
              <ChatMessage
                key={msg.id}
                message={msg}
                onReanalyze={handleReanalyze}
              />
            ))}
            {loading && (
              <div className="msg msg--ai">
                <div className="msg__bubble">
                  <div className="skeleton">
                    <div className="skeleton__inner">
                      <div className="analyzing-status">
                        <div className="analyzing-dot"></div>
                        <div className="analyzing-dot"></div>
                        <div className="analyzing-dot"></div>
                        <span>Analyzing content…</span>
                      </div>
                      <div className="skeleton__block"></div>
                      <div className="skeleton__line skeleton__line--long"></div>
                      <div className="skeleton__line skeleton__line--medium"></div>
                      <div className="skeleton__line skeleton__line--short"></div>
                      <div className="skeleton__row">
                        <div className="skeleton__chip"></div>
                        <div className="skeleton__chip"></div>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            )}
          </>
        )}
        <div ref={chatEndRef} />
      </main>

      <InputBar onSend={handleSend} disabled={loading} />
    </div>
  )
}

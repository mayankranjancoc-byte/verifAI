import { useState, useRef, useEffect } from 'react'
import InputBar from './components/InputBar'
import ChatMessage from './components/ChatMessage'
import Welcome from './components/Welcome'
import HistorySidebar from './components/HistorySidebar'

// In dev: empty string (Vite proxy handles /api/* → localhost:8001)
// In prod: full Render backend URL (e.g. https://verifai-9uho.onrender.com)
const API_BASE = import.meta.env.VITE_API_URL || ''
const API_URL = `${API_BASE}/api/analyze`

function loadHistory() {
  try {
    return JSON.parse(localStorage.getItem('verifai_history') || '[]')
  } catch { return [] }
}

function saveToHistory(query, result) {
  const history = loadHistory()
  history.unshift({
    id: Date.now(),
    query: query.substring(0, 100),
    verdict: result.verdict,
    reality_score: result.reality_score,
    timestamp: new Date().toISOString(),
    fullResult: result,
  })
  localStorage.setItem('verifai_history', JSON.stringify(history.slice(0, 50)))
}

export default function App() {
  const [messages, setMessages] = useState([])
  const [loading, setLoading] = useState(false)
  const [historyOpen, setHistoryOpen] = useState(false)
  const [history, setHistory] = useState(loadHistory)
  const chatEndRef = useRef(null)

  const scrollToBottom = () => {
    chatEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  useEffect(() => {
    scrollToBottom()
  }, [messages, loading])

  const handleSend = async (input, file, cachedClaims) => {
    if (!input.trim() && !file) return

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
      if (file) formData.append('file', file)
      if (cachedClaims) formData.append('reanalyze', cachedClaims)

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

      // Save to history
      saveToHistory(input, data)
      setHistory(loadHistory())
    } catch (err) {
      console.error('Analysis failed:', err)
      const errorMsg = {
        id: Date.now() + 1,
        role: 'ai',
        data: {
          verdict: 'ERROR',
          reality_score: 0,
          claims: [],
          key_insights: [{ icon: 'error', text: `Analysis failed: ${err.message}` }],
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

  const handleReanalyze = async (originalContent, cachedClaims) => {
    if (!cachedClaims) {
      // Fallback: no cached claims, just re-send to /api/analyze
      handleSend(originalContent)
      return
    }

    setLoading(true)
    try {
      const formData = new FormData()
      formData.append('content', originalContent || '')
      formData.append('cached_claims', cachedClaims)

      const res = await fetch(`${API_BASE}/api/reverify`, {
        method: 'POST',
        body: formData
      })

      if (!res.ok) throw new Error(`Server error: ${res.status}`)
      const freshData = await res.json()

      // Merge fresh verification results into the last AI message
      setMessages(prev => {
        const updated = [...prev]
        // Find the last AI message
        for (let i = updated.length - 1; i >= 0; i--) {
          if (updated[i].role === 'ai' && updated[i].data) {
            const merged = {
              ...updated[i].data,
              verdict: freshData.verdict,
              reality_score: freshData.reality_score,
              score_breakdown: freshData.score_breakdown,
              verified_claims: freshData.verified_claims,
              trust_trail: freshData.trust_trail,
              sources: freshData.sources,
              analysis_timestamp: freshData.analysis_timestamp,
              verification_method: freshData.verification_method,
              _cached_claims: freshData._cached_claims,
            }
            updated[i] = { ...updated[i], data: merged, timestamp: new Date() }
            break
          }
        }
        return updated
      })

      // Update history with fresh data
      saveToHistory(originalContent, { ...messages[messages.length - 1]?.data, ...freshData })
      setHistory(loadHistory())
    } catch (err) {
      console.error('Re-verify failed:', err)
    } finally {
      setLoading(false)
    }
  }

  const handleChipClick = (text) => {
    handleSend(text)
  }

  const handleHistorySelect = (item) => {
    if (item.fullResult) {
      const userMsg = {
        id: Date.now(),
        role: 'user',
        content: item.query,
        timestamp: new Date(item.timestamp)
      }
      const aiMsg = {
        id: Date.now() + 1,
        role: 'ai',
        data: item.fullResult,
        timestamp: new Date(item.timestamp)
      }
      setMessages([userMsg, aiMsg])
    }
  }

  const handleClearHistory = () => {
    localStorage.removeItem('verifai_history')
    setHistory([])
  }

  return (
    <div className="app">
      <header className="header">
        <div className="header__brand">
          <button className="icon-btn" onClick={() => setHistoryOpen(true)}>
            <span className="material-symbols-outlined">menu</span>
          </button>
          <h1 className="header__logo">VerifAI</h1>
        </div>
        <div className="header__actions">
          <button className="icon-btn" onClick={() => setHistoryOpen(true)}>
            <span className="material-symbols-outlined">history</span>
          </button>
          <button className="icon-btn">
            <span className="material-symbols-outlined">settings</span>
          </button>
        </div>
      </header>

      <HistorySidebar
        open={historyOpen}
        onClose={() => setHistoryOpen(false)}
        history={history}
        onSelect={handleHistorySelect}
        onClear={handleClearHistory}
      />

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
                        <span>Verifying across real sources…</span>
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

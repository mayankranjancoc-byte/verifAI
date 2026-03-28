import { useState } from 'react'

export default function ActionButtons({ sources, onReanalyze, timestamp }) {
  const [showSources, setShowSources] = useState(false)

  const timeAgo = timestamp ? getTimeAgo(timestamp) : null

  const handleShare = async () => {
    if (navigator.share) {
      try {
        await navigator.share({
          title: 'VerifAI Analysis',
          text: 'Check this fact-check report from VerifAI',
        })
      } catch (e) { /* cancelled */ }
    }
  }

  return (
    <>
      <div className="actions">
        <button
          className="action-btn action-btn--default"
          onClick={() => setShowSources(!showSources)}
        >
          <span className="material-symbols-outlined">visibility</span>
          {showSources ? 'Hide Sources' : 'View Sources'}
        </button>
        <button className="action-btn action-btn--default" onClick={handleShare}>
          <span className="material-symbols-outlined">share</span>
          Share
        </button>
        <button className="action-btn action-btn--primary" onClick={onReanalyze}>
          <span className="material-symbols-outlined">refresh</span>
          Re-analyze
        </button>
      </div>

      {timeAgo && (
        <div className="actions__timestamp">
          <span className="material-symbols-outlined" style={{ fontSize: 12 }}>schedule</span>
          Last verified: {timeAgo}
        </div>
      )}

      {showSources && sources && sources.length > 0 && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '6px', marginTop: '8px' }}>
          {sources.map((s, i) => (
            <a
              key={i}
              href={s.url}
              target="_blank"
              rel="noopener noreferrer"
              style={{
                display: 'flex', alignItems: 'center', gap: '6px',
                padding: '8px 12px', background: 'var(--surface-low)',
                borderRadius: 'var(--radius-md)', fontSize: '12px',
                color: 'var(--accent)', textDecoration: 'none',
                transition: 'background 0.15s ease'
              }}
            >
              <span className="material-symbols-outlined" style={{ fontSize: '14px' }}>open_in_new</span>
              {s.name || new URL(s.url).hostname}
            </a>
          ))}
        </div>
      )}
    </>
  )
}

function getTimeAgo(timestamp) {
  const now = new Date()
  const then = new Date(timestamp)
  const diff = Math.floor((now - then) / 1000)
  if (diff < 60) return 'just now'
  if (diff < 3600) return `${Math.floor(diff / 60)} min ago`
  if (diff < 86400) return `${Math.floor(diff / 3600)}h ago`
  return then.toLocaleDateString()
}

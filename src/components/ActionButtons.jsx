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

  // Safely extract hostname from URL
  const getHostname = (url) => {
    try {
      return new URL(url).hostname.replace('www.', '')
    } catch {
      return url
    }
  }

  // Filter valid sources (must have url)
  const validSources = (sources || []).filter(s => s && s.url)

  return (
    <>
      <div className="actions">
        <button
          className="action-btn action-btn--default"
          onClick={() => setShowSources(!showSources)}
        >
          <span className="material-symbols-outlined">visibility</span>
          {showSources ? 'Hide Sources' : 'View Sources'}
          {validSources.length > 0 && (
            <span style={{
              background: 'var(--accent)',
              color: '#fff',
              borderRadius: '10px',
              padding: '1px 6px',
              fontSize: '10px',
              marginLeft: '4px',
              fontWeight: 600,
            }}>
              {validSources.length}
            </span>
          )}
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

      {showSources && (
        <div className="sources-panel">
          {validSources.length === 0 ? (
            <div className="sources-panel__empty">
              <span className="material-symbols-outlined">search_off</span>
              No external sources found for this analysis
            </div>
          ) : (
            validSources.map((s, i) => (
              <a
                key={i}
                href={s.url}
                target="_blank"
                rel="noopener noreferrer"
                className="sources-panel__item"
              >
                <span className="material-symbols-outlined" style={{ fontSize: '16px', color: 'var(--accent)' }}>open_in_new</span>
                <div className="sources-panel__info">
                  <span className="sources-panel__name">{s.name || getHostname(s.url)}</span>
                  <span className="sources-panel__url">{getHostname(s.url)}</span>
                </div>
              </a>
            ))
          )}
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

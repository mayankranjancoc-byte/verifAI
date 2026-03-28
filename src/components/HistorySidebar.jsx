export default function HistorySidebar({ open, onClose, history, onSelect, onClear }) {
  if (!open) return null

  return (
    <>
      <div className="history-overlay" onClick={onClose} />
      <div className={`history-sidebar ${open ? 'history-sidebar--open' : ''}`}>
        <div className="history-sidebar__header">
          <h2 className="history-sidebar__title">Analysis History</h2>
          <button className="icon-btn" onClick={onClose}>
            <span className="material-symbols-outlined">close</span>
          </button>
        </div>

        {history.length === 0 ? (
          <div className="history-sidebar__empty">
            <span className="material-symbols-outlined" style={{ fontSize: 32, color: 'var(--text-tertiary)' }}>history</span>
            <p>No analyses yet</p>
          </div>
        ) : (
          <>
            <div className="history-sidebar__list">
              {history.map((item) => (
                <button
                  key={item.id}
                  className="history-item"
                  onClick={() => { onSelect(item); onClose(); }}
                >
                  <div className="history-item__top">
                    <span className={`history-item__verdict history-item__verdict--${(item.verdict || '').toLowerCase()}`}>
                      {item.verdict}
                    </span>
                    <span className="history-item__score">{item.reality_score}/100</span>
                  </div>
                  <div className="history-item__query">{item.query}</div>
                  <div className="history-item__time">
                    {new Date(item.timestamp).toLocaleString()}
                  </div>
                </button>
              ))}
            </div>
            <button className="history-sidebar__clear" onClick={onClear}>
              <span className="material-symbols-outlined" style={{ fontSize: 14 }}>delete</span>
              Clear History
            </button>
          </>
        )}
      </div>
    </>
  )
}

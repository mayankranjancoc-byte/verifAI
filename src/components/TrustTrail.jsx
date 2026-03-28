export default function TrustTrail({ items }) {
  if (!items || items.length === 0) return null

  return (
    <div className="trust-trail-section">
      <div className="trust-trail-section__label">TRUST TRAIL</div>
      <div className="trust-trail">
        {items.map((item, i) => {
          const stance = (item.stance || 'neutral').toLowerCase()
          const isSupporting = stance === 'supporting' || stance === 'supports'
          const isContradicting = stance === 'contradicting' || stance === 'contradicts'
          const stanceClass = isSupporting ? 'supporting' : isContradicting ? 'contradicting' : 'neutral'
          const stanceLabel = isSupporting ? 'Supporting' : isContradicting ? 'Contradicting' : 'Neutral'
          const icon = isSupporting ? 'verified' : isContradicting ? 'cancel' : 'help'
          const sourceName = item.name || item.source || 'Source'
          const url = item.url || ''
          const excerpt = item.excerpt || ''

          return (
            <div key={i} className={`trust-card trust-card--${stanceClass}`}>
              <span className="material-symbols-outlined filled">{icon}</span>
              <div className="trust-card__info">
                <div className="trust-card__label">{stanceLabel}</div>
                {url ? (
                  <a
                    href={url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="trust-card__name trust-card__link"
                    title={url}
                  >
                    {sourceName}
                    <span className="material-symbols-outlined" style={{ fontSize: 11, marginLeft: 3, verticalAlign: 'middle' }}>open_in_new</span>
                  </a>
                ) : (
                  <div className="trust-card__name">{sourceName}</div>
                )}
                {excerpt && (
                  <div className="trust-card__excerpt">{excerpt}</div>
                )}
              </div>
            </div>
          )
        })}
      </div>
    </div>
  )
}

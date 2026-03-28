export default function TrustTrail({ items }) {
  return (
    <div className="trust-trail">
      {items.map((item, i) => (
        <div
          key={i}
          className={`trust-card trust-card--${item.stance}`}
        >
          <span className="material-symbols-outlined filled">
            {item.stance === 'supporting' ? 'verified' : 'cancel'}
          </span>
          <div className="trust-card__info">
            <div className="trust-card__label">
              {item.stance === 'supporting' ? 'Supporting' : 'Contradicting'}
            </div>
            <div className="trust-card__name">{item.name}</div>
          </div>
        </div>
      ))}
    </div>
  )
}

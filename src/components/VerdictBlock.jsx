export default function VerdictBlock({ score, verdict }) {
  const v = verdict.toLowerCase()

  const getClass = () => {
    switch (v) {
      case 'false': return 'false'
      case 'misleading': return 'misleading'
      case 'true': return 'true'
      case 'unverified': return 'unverified'
      default: return 'unverified'
    }
  }

  const cls = getClass()

  return (
    <div className="verdict">
      <div>
        <div className="verdict__score-label">Reality Score</div>
        <div className="verdict__score">
          <span className={`verdict__number verdict__number--${cls}`}>
            {score ?? '—'}
          </span>
          <span className="verdict__total">/100</span>
        </div>
      </div>
      <div className={`verdict__badge verdict__badge--${cls}`}>
        {verdict.toUpperCase()}
      </div>
    </div>
  )
}

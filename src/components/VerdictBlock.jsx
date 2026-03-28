import ScoreBreakdown from './ScoreBreakdown'

export default function VerdictBlock({ score, verdict, scoreBreakdown, verifiedClaims }) {
  const v = (verdict || '').toLowerCase()

  const getClass = () => {
    switch (v) {
      case 'false': case 'mostly false': return 'false'
      case 'misleading': return 'misleading'
      case 'true': case 'mostly true': return 'true'
      case 'unverifiable': case 'unverified': return 'unverified'
      default: return 'unverified'
    }
  }

  const cls = getClass()

  return (
    <div className="verdict-section">
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
          {(verdict || 'UNVERIFIED').toUpperCase()}
        </div>
      </div>

      {/* Score Breakdown — standalone component */}
      <ScoreBreakdown scoreBreakdown={scoreBreakdown} />
    </div>
  )
}

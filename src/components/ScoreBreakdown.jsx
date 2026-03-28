import { useState } from 'react'

export default function ScoreBreakdown({ scoreBreakdown }) {
  const [expanded, setExpanded] = useState(false)

  if (!scoreBreakdown) return null

  const { formula, claims_average, manipulation_penalty, per_claim_scores } = scoreBreakdown

  return (
    <div className="score-breakdown">
      <button className="score-breakdown__toggle" onClick={() => setExpanded(!expanded)}>
        <span className="material-symbols-outlined" style={{ fontSize: 14 }}>
          {expanded ? 'expand_less' : 'expand_more'}
        </span>
        {expanded ? 'Hide calculation' : 'How was this calculated?'}
      </button>

      {expanded && (
        <div className="score-breakdown__content">
          {/* Formula explanation */}
          {formula && (
            <div className="score-breakdown__formula">
              <span className="material-symbols-outlined" style={{ fontSize: 14 }}>calculate</span>
              <span>{formula}</span>
            </div>
          )}

          {/* Base score + penalty */}
          <div className="score-breakdown__row">
            <span>Claims average:</span>
            <strong>{claims_average ?? 0}%</strong>
          </div>

          {/* Visual bar for claims average */}
          <div className="score-breakdown__bar-track">
            <div
              className="score-breakdown__bar-fill score-breakdown__bar-fill--base"
              style={{ width: `${Math.min(100, claims_average || 0)}%` }}
            />
          </div>

          <div className="score-breakdown__row score-breakdown__row--penalty">
            <span>Manipulation penalty:</span>
            <strong className="score-breakdown__penalty-value">−{manipulation_penalty ?? 0}%</strong>
          </div>

          {/* Per-claim breakdown table */}
          {per_claim_scores && per_claim_scores.length > 0 && (
            <div className="score-breakdown__claims">
              <div className="score-breakdown__claims-title">PER-CLAIM SCORES</div>
              {per_claim_scores.map((item, i) => {
                const statusClass = item.status === 'confirmed' ? 'confirmed'
                  : item.status === 'contradicted' ? 'contradicted'
                  : 'unverifiable'
                const icon = item.status === 'confirmed' ? '✅'
                  : item.status === 'contradicted' ? '❌'
                  : '⚠️'

                return (
                  <div key={i} className={`score-breakdown__claim-row score-breakdown__claim-row--${statusClass}`}>
                    <div className="score-breakdown__claim-info">
                      <span className="score-breakdown__claim-icon">{icon}</span>
                      <span className="score-breakdown__claim-text">{item.claim}</span>
                    </div>
                    <div className="score-breakdown__claim-score">
                      <span className={`score-breakdown__claim-value score-breakdown__claim-value--${statusClass}`}>
                        {item.score}%
                      </span>
                    </div>
                  </div>
                )
              })}
            </div>
          )}
        </div>
      )}
    </div>
  )
}

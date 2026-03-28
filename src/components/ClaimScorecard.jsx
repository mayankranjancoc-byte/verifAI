export default function ClaimScorecard({ verifiedClaims }) {
  if (!verifiedClaims || verifiedClaims.length === 0) return null

  return (
    <div className="scorecard">
      <div className="scorecard__title">PER-CLAIM VERIFICATION</div>
      {verifiedClaims.map((claim, i) => {
        const icon = claim.status === 'confirmed' ? '✅' :
                     claim.status === 'contradicted' ? '❌' : '⚠️'
        const cls = claim.status || 'unverifiable'
        return (
          <div key={i} className={`scorecard__row scorecard__row--${cls}`}>
            <div className="scorecard__claim">
              <span className="scorecard__icon">{icon}</span>
              <span className="scorecard__text">{claim.text}</span>
            </div>
            <div className="scorecard__sources">
              {(claim.confirmed_by || []).slice(0, 2).map((s, j) => (
                <a key={`c${j}`} href={s.url} target="_blank" rel="noopener noreferrer"
                   className="scorecard__badge scorecard__badge--confirm">
                  {s.source}
                </a>
              ))}
              {(claim.contradicted_by || []).slice(0, 2).map((s, j) => (
                <a key={`d${j}`} href={s.url} target="_blank" rel="noopener noreferrer"
                   className="scorecard__badge scorecard__badge--deny">
                  {s.source}
                </a>
              ))}
              {(claim.corroborating || []).slice(0, 2).map((s, j) => (
                <a key={`n${j}`} href={s.url} target="_blank" rel="noopener noreferrer"
                   className="scorecard__badge scorecard__badge--neutral">
                  {s.source}
                </a>
              ))}
              {claim.unverifiable && !(claim.corroborating || []).length && (
                <span className="scorecard__badge scorecard__badge--unknown">No sources found</span>
              )}
            </div>
          </div>
        )
      })}
    </div>
  )
}

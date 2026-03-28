export default function HeatmapBlock({ claims }) {
  return (
    <div className="heatmap">
      {claims.map((claim, i) => (
        <div key={i}>
          <div className="heatmap__text-container">
            <RenderHighlightedText text={claim.text} highlights={claim.highlights || []} />
          </div>
          {claim.virality_spike && (
            <div className="heatmap__spike">
              <span className="material-symbols-outlined">trending_up</span>
              <span>{claim.virality_spike}</span>
            </div>
          )}
        </div>
      ))}
    </div>
  )
}

function RenderHighlightedText({ text, highlights }) {
  if (!highlights || highlights.length === 0) {
    return <span>{text}</span>
  }

  // Sort highlights by position in text
  const sorted = [...highlights].sort((a, b) => {
    const posA = text.toLowerCase().indexOf(a.word.toLowerCase())
    const posB = text.toLowerCase().indexOf(b.word.toLowerCase())
    return posA - posB
  })

  const parts = []
  let lastIndex = 0

  sorted.forEach((h, i) => {
    const idx = text.toLowerCase().indexOf(h.word.toLowerCase(), lastIndex)
    if (idx === -1) return

    // Text before highlight
    if (idx > lastIndex) {
      parts.push(<span key={`t${i}`}>{text.slice(lastIndex, idx)}</span>)
    }

    // Highlighted word
    const riskLevel = h.risk > 0.7 ? 'high' : 'medium'
    parts.push(
      <span
        key={`h${i}`}
        className={`heatmap__highlight heatmap__highlight--${riskLevel}`}
        title={h.reason}
      >
        {text.slice(idx, idx + h.word.length)}
        <span className="material-symbols-outlined filled" style={{ fontSize: '12px', marginLeft: '2px', verticalAlign: 'middle' }}>info</span>
      </span>
    )

    lastIndex = idx + h.word.length
  })

  // Remaining text
  if (lastIndex < text.length) {
    parts.push(<span key="rest">{text.slice(lastIndex)}</span>)
  }

  return <>{parts}</>
}

import { useState } from 'react'

const TACTIC_COLORS = {
  fear_injection: { bg: '#FDE8E6', color: '#D93025', label: 'Fear' },
  outrage_amplification: { bg: '#FDE8E6', color: '#B71C1C', label: 'Outrage' },
  false_urgency: { bg: '#FFF3E0', color: '#E65100', label: 'Urgency' },
  authority_fabrication: { bg: '#FEF6E0', color: '#E8A800', label: 'Authority' },
  emotional_loading: { bg: '#F3E5F5', color: '#7B1FA2', label: 'Emotional' },
}

export default function ClaimHeatmap({ content, emotionExploit }) {
  if (!content || !emotionExploit?.tactics) return null

  const allPhrases = []
  const tactics = emotionExploit.tactics || {}

  Object.entries(tactics).forEach(([tacticName, data]) => {
    (data.trigger_phrases || []).forEach(phrase => {
      if (phrase && content.toLowerCase().includes(phrase.toLowerCase())) {
        allPhrases.push({
          phrase,
          tactic: tacticName,
          score: data.score || 0,
          ...TACTIC_COLORS[tacticName] || TACTIC_COLORS.emotional_loading,
        })
      }
    })
  })

  if (allPhrases.length === 0) return null

  // Sort by position in text
  allPhrases.sort((a, b) => {
    return content.toLowerCase().indexOf(a.phrase.toLowerCase()) -
           content.toLowerCase().indexOf(b.phrase.toLowerCase())
  })

  // Build highlighted spans
  const parts = []
  let lastIdx = 0
  const used = new Set()

  allPhrases.forEach((p, i) => {
    const idx = content.toLowerCase().indexOf(p.phrase.toLowerCase(), lastIdx)
    if (idx === -1 || used.has(p.phrase.toLowerCase())) return
    used.add(p.phrase.toLowerCase())

    if (idx > lastIdx) {
      parts.push(<span key={`t${i}`}>{content.slice(lastIdx, idx)}</span>)
    }

    parts.push(
      <HeatmapWord
        key={`h${i}`}
        word={content.slice(idx, idx + p.phrase.length)}
        tactic={p.label}
        score={p.score}
        bg={p.bg}
        color={p.color}
      />
    )
    lastIdx = idx + p.phrase.length
  })

  if (lastIdx < content.length) {
    parts.push(<span key="rest">{content.slice(lastIdx)}</span>)
  }

  return (
    <div className="claim-heatmap">
      <div className="claim-heatmap__label">MANIPULATION HEATMAP</div>
      <div className="claim-heatmap__text">{parts}</div>
      <div className="claim-heatmap__legend">
        {Object.entries(TACTIC_COLORS).map(([key, val]) => (
          <span key={key} className="claim-heatmap__legend-item">
            <span className="claim-heatmap__legend-dot" style={{ background: val.color }} />
            {val.label}
          </span>
        ))}
      </div>
    </div>
  )
}

function HeatmapWord({ word, tactic, score, bg, color }) {
  const [hover, setHover] = useState(false)
  return (
    <span
      className="claim-heatmap__word"
      style={{ background: bg, color, borderBottomColor: color }}
      onMouseEnter={() => setHover(true)}
      onMouseLeave={() => setHover(false)}
    >
      {word}
      {hover && (
        <span className="claim-heatmap__tooltip">
          ⚠️ {tactic} — Score: {score}/10
        </span>
      )}
    </span>
  )
}

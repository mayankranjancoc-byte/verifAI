import { useState } from 'react'

const TACTIC_COLORS = {
  fear_injection: { bg: '#FDE8E6', color: '#D93025', label: 'Fear' },
  outrage_amplification: { bg: '#FDE8E6', color: '#B71C1C', label: 'Outrage' },
  false_urgency: { bg: '#FFF3E0', color: '#E65100', label: 'Urgency' },
  authority_fabrication: { bg: '#FEF6E0', color: '#E8A800', label: 'Authority' },
  emotional_loading: { bg: '#F3E5F5', color: '#7B1FA2', label: 'Emotional' },
}

// Normalize tactic keys — LLM sometimes returns slightly different keys
function normalizeTacticKey(key) {
  const k = key.toLowerCase().replace(/[\s-]/g, '_')
  if (k.includes('fear')) return 'fear_injection'
  if (k.includes('outrage')) return 'outrage_amplification'
  if (k.includes('urgency')) return 'false_urgency'
  if (k.includes('authority')) return 'authority_fabrication'
  if (k.includes('emotion') || k.includes('loading')) return 'emotional_loading'
  return k
}

export default function ClaimHeatmap({ content, emotionExploit }) {
  if (!content || !emotionExploit?.tactics) return null

  const allPhrases = []
  const tactics = emotionExploit.tactics || {}

  Object.entries(tactics).forEach(([tacticName, data]) => {
    const normalizedKey = normalizeTacticKey(tacticName)
    const colorInfo = TACTIC_COLORS[normalizedKey] || TACTIC_COLORS.emotional_loading
    ;(data.trigger_phrases || []).forEach(phrase => {
      if (phrase && phrase.length > 1 && content.toLowerCase().includes(phrase.toLowerCase())) {
        allPhrases.push({
          phrase,
          tactic: normalizedKey,
          score: data.score || 0,
          ...colorInfo,
        })
      }
    })
  })

  // If no trigger phrases found in the original text, don't render
  if (allPhrases.length === 0) return null

  // Sort by position in text (earliest first)
  allPhrases.sort((a, b) => {
    return content.toLowerCase().indexOf(a.phrase.toLowerCase()) -
           content.toLowerCase().indexOf(b.phrase.toLowerCase())
  })

  // Build highlighted spans — match entire phrases contiguously
  const parts = []
  let lastIdx = 0
  const used = new Set()

  allPhrases.forEach((p, i) => {
    const idx = content.toLowerCase().indexOf(p.phrase.toLowerCase(), lastIdx)
    if (idx === -1 || used.has(p.phrase.toLowerCase())) return
    used.add(p.phrase.toLowerCase())

    // Text before this phrase
    if (idx > lastIdx) {
      parts.push(<span key={`t${i}`}>{content.slice(lastIdx, idx)}</span>)
    }

    // Highlighted phrase (full phrase, not split by words)
    parts.push(
      <HeatmapPhrase
        key={`h${i}`}
        text={content.slice(idx, idx + p.phrase.length)}
        tactic={p.label}
        score={p.score}
        bg={p.bg}
        color={p.color}
      />
    )
    lastIdx = idx + p.phrase.length
  })

  // Remaining unhighlighted text
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

function HeatmapPhrase({ text, tactic, score, bg, color }) {
  const [hover, setHover] = useState(false)
  return (
    <span
      className="claim-heatmap__word"
      style={{
        background: bg,
        color,
        borderBottom: `2px solid ${color}`,
        padding: '2px 4px',
        borderRadius: '3px',
        position: 'relative',
        cursor: 'help',
      }}
      onMouseEnter={() => setHover(true)}
      onMouseLeave={() => setHover(false)}
    >
      {text}
      <span className="material-symbols-outlined filled" style={{ fontSize: '11px', marginLeft: '2px', verticalAlign: 'middle', opacity: 0.7 }}>info</span>
      {hover && (
        <span className="claim-heatmap__tooltip">
          ⚠️ {tactic} — Score: {score}/10
        </span>
      )}
    </span>
  )
}

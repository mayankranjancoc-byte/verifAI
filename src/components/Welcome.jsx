export default function Welcome({ onChipClick }) {
  const suggestions = [
    'Is "5G causes COVID" still spreading?',
    'Check this WhatsApp forward',
    'Verify a news headline',
    'क्या ये खबर सच है?',
  ]

  return (
    <div className="welcome">
      <div className="welcome__icon">
        <span className="material-symbols-outlined filled">verified</span>
      </div>
      <h2 className="welcome__title">What do you want to verify?</h2>
      <p className="welcome__subtitle">
        Paste any news, URL, image, or voice note. VerifAI will check it
        against real sources and give you the truth — with a side of humor.
      </p>
      <div className="welcome__chips">
        {suggestions.map((s, i) => (
          <button
            key={i}
            className="welcome__chip"
            onClick={() => onChipClick(s)}
          >
            {s}
          </button>
        ))}
      </div>
    </div>
  )
}

export default function HumorBlock({ data }) {
  const { joke, explanation } = data

  return (
    <div className="humor">
      <span className="humor__emoji">💀</span>
      <div>
        <p className="humor__text">{joke}</p>
        {explanation && (
          <p className="humor__explanation">{explanation}</p>
        )}
      </div>
    </div>
  )
}

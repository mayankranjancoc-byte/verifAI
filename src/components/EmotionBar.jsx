export default function EmotionBar({ data }) {
  const { intensity, label } = data
  const level = intensity >= 70 ? 'high' : intensity >= 40 ? 'medium' : 'low'

  return (
    <div className="emotion">
      <div className="emotion__header">
        <span className="emotion__label">Emotion Analysis</span>
        <span className={`emotion__value emotion__value--${level}`}>
          {intensity}% Emotional Intensity
        </span>
      </div>
      <div className="emotion__track">
        <div
          className={`emotion__fill emotion__fill--${level}`}
          style={{ width: `${intensity}%` }}
        />
      </div>
      {label && <p className="emotion__desc">{label}</p>}
    </div>
  )
}

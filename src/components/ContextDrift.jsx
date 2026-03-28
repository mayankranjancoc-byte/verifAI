export default function ContextDrift({ data }) {
  return (
    <div className="context-drift">
      <span className="material-symbols-outlined filled">warning</span>
      <p className="context-drift__text">{data.message}</p>
    </div>
  )
}

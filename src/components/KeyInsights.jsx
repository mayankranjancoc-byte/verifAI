export default function KeyInsights({ items }) {
  return (
    <div className="insights">
      <h3 className="insights__title">Key Intelligence Insights</h3>
      <ul className="insights__list">
        {items.map((item, i) => (
          <li key={i} className="insights__item">
            <span className={`material-symbols-outlined filled`}>
              {item.icon === 'check' || item.icon === 'check_circle' ? 'check_circle' :
               item.icon === 'error' ? 'error' :
               item.icon === 'warning' ? 'warning' : 'check_circle'}
            </span>
            <span>{item.text}</span>
          </li>
        ))}
      </ul>
    </div>
  )
}

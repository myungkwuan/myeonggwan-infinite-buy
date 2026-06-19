import { modeEasy } from '../format.js'

export function ModeBadge({ mode }) {
  const cls = mode === '후반전' ? 'hoo' : mode === '쿼터' ? 'quarter' : 'jeon'
  return (
    <span className={'badge ' + cls}>
      {modeEasy(mode)}<i>{mode}</i>
    </span>
  )
}

export function ProgressBar({ value, max }) {
  const m = max || 40
  const w = Math.max(0, Math.min(100, (Number(value) / m) * 100))
  return (
    <div className="progress">
      <div className="progress-head">
        <span>진행 회차</span>
        <span className="num">T {Number(value).toFixed(1)} / {m}</span>
      </div>
      <div className="progress-track">
        <div className="progress-fill" style={{ width: w + '%' }} />
      </div>
    </div>
  )
}

export function StatCard({ label, value, sub, cls }) {
  return (
    <div className="stat">
      <div className="stat-label">{label}</div>
      <div className={'stat-value num ' + (cls || '')}>{value}</div>
      {sub != null && <div className="stat-sub num">{sub}</div>}
    </div>
  )
}

export function Empty({ text }) {
  return <div className="empty">{text}</div>
}

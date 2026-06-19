import { useEffect, useState } from 'react'
import { api } from '../api.js'
import { krw, pct, usd } from '../format.js'
import { StatCard } from '../components/ui.jsx'

function ProfitBars({ cycles }) {
  if (!cycles.length) return null
  const W = 700, H = 200, padL = 40, padR = 12, padT = 14, padB = 26
  const plotW = W - padL - padR, plotH = H - padT - padB
  const vals = cycles.map((c) => c.final_profit_pct ?? 0)
  let max = Math.max(...vals, 5), min = Math.min(...vals, -5)
  const span = max - min || 1
  const y0 = padT + (max / span) * plotH       // 0% 기준선
  const bw = Math.min(46, (plotW / cycles.length) * 0.6)
  return (
    <svg className="bars-svg" viewBox={`0 0 ${W} ${H}`} preserveAspectRatio="xMidYMid meet">
      <line x1={padL} y1={y0} x2={W - padR} y2={y0} className="chart-grid" />
      <text x={padL - 6} y={y0 + 4} textAnchor="end" className="chart-axis">0%</text>
      {cycles.map((c, i) => {
        const cx = padL + (plotW / cycles.length) * (i + 0.5)
        const v = c.final_profit_pct ?? 0
        const yv = padT + ((max - v) / span) * plotH
        const top = Math.min(yv, y0), h = Math.abs(yv - y0)
        const up = v >= 0
        return (
          <g key={c.id}>
            <rect x={cx - bw / 2} y={top} width={bw} height={Math.max(h, 1)} rx="3"
                  className={up ? 'bar-up' : 'bar-down'} />
            <text x={cx} y={up ? top - 5 : top + h + 13} textAnchor="middle" className="bar-val">
              {v >= 0 ? '+' : ''}{v.toFixed(1)}%
            </text>
            <text x={cx} y={H - 8} textAnchor="middle" className="chart-axis">#{c.id}</text>
          </g>
        )
      })}
    </svg>
  )
}

export default function StatsTab() {
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [d, setD] = useState(null)

  useEffect(() => {
    (async () => {
      setLoading(true); setError(null)
      try { setD(await api.statsSummary()) }
      catch (e) { setError(e.message) }
      finally { setLoading(false) }
    })()
  }, [])

  if (loading) return <div className="center"><div className="spin" /></div>
  if (error) return <div className="error-card">{error}</div>
  if (!d) return null

  const cumCls = d.cum_profit_krw >= 0 ? 'pos' : 'neg'

  return (
    <div className="stats">
      <div className="grid2">
        <StatCard label="총 사이클" value={d.total_cycles + '개'} sub={'진행 ' + d.active_cycles + ' · 완료 ' + d.closed_cycles} />
        <StatCard label="평균 회차" value={d.avg_turns != null ? 'T ' + d.avg_turns : '—'} sub="완료 사이클 기준" />
        <StatCard label="평균 수익률" value={d.avg_profit_pct != null ? pct(d.avg_profit_pct) : '—'}
                  cls={d.avg_profit_pct != null ? (d.avg_profit_pct >= 0 ? 'pos' : 'neg') : ''} sub="완료 사이클" />
        <StatCard label="누적 수익금" value={krw(d.cum_profit_krw)} cls={cumCls}
                  sub={d.best_profit_pct != null ? '최고 ' + pct(d.best_profit_pct) : '—'} />
      </div>

      {d.current && (
        <div className="cur-box">
          <div className="cur-title">진행 중 · 사이클 #{d.current.id}</div>
          <div className="cur-grid num">
            <div><span>회차</span><b>T {Number(d.current.turn_number).toFixed(1)}</b></div>
            <div><span>평가손익</span><b className={(d.current.profit_pct ?? 0) >= 0 ? 'up' : 'down'}>{pct(d.current.profit_pct)}</b></div>
            <div><span>평가액</span><b>{d.current.eval_value_krw != null ? krw(d.current.eval_value_krw) : '—'}</b></div>
          </div>
        </div>
      )}

      <div className="section-title" style={{ marginTop: 14 }}>사이클별 수익률</div>
      {d.cycles.length ? (
        <div className="chart-wrap"><ProfitBars cycles={d.cycles} /></div>
      ) : (
        <div className="empty">완료된 사이클이 아직 없어요. 사이클을 종료하면 여기에 쌓입니다.</div>
      )}
    </div>
  )
}

import { useEffect, useState } from 'react'
import { api } from '../api.js'
import { usd, pct } from '../format.js'
import SvgChart from '../components/SvgChart.jsx'

export default function ChartTab() {
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [hasSession, setHasSession] = useState(false)
  const [points, setPoints] = useState([])
  const [targetPct, setTargetPct] = useState(20)
  const [hover, setHover] = useState(null)

  useEffect(() => {
    (async () => {
      setLoading(true); setError(null)
      try {
        const cur = await api.currentSession()
        if (!cur.session) { setHasSession(false); setLoading(false); return }
        setHasSession(true)
        const list = await api.dailyList()
        setPoints(list.points || [])
        setTargetPct(list.target_pct ?? 20)
      } catch (e) {
        setError(e.message)
      } finally {
        setLoading(false)
      }
    })()
  }, [])

  if (loading) return <div className="center"><div className="spin" /></div>
  if (error) return <div className="error-card">{error}</div>
  if (!hasSession) return <div className="center">활성 사이클이 없어요. 홈에서 사이클을 먼저 시작하세요.</div>
  if (points.length === 0)
    return <div className="center">아직 계산 이력이 없어요.<br />홈 탭에서 계산하면 여기에 추이가 쌓입니다.</div>

  const idx = hover == null ? points.length - 1 : hover
  const p = points[idx]
  const cur = p.soxl_close
  const avg = p.avg_price_usd
  const target = p.target_price
  const toTarget = cur && target ? (target / cur - 1) * 100 : null

  return (
    <div className="chart">
      <div className="chart-readout">
        <div className="ro-date">{p.date}{hover == null ? ' · 최신' : ''}</div>
        <div className="ro-grid">
          <div><span>가격</span><b className="num c-price">{usd(cur)}</b></div>
          <div><span>평단</span><b className="num c-avg">{avg ? usd(avg) : '—'}</b></div>
          <div><span>익절 +{targetPct}%</span><b className="num c-target">{target ? usd(target) : '—'}</b></div>
        </div>
      </div>

      <div className="chart-legend">
        <span className="lg lg-price">가격</span>
        <span className="lg lg-avg">평단</span>
        <span className="lg lg-target">익절 +{targetPct}%</span>
        <span className="lg lg-buy">▲ 매수</span>
        <span className="lg lg-sell">▼ 매도</span>
      </div>

      <div className="chart-wrap">
        <SvgChart points={points} hoverIdx={hover} onHover={setHover} />
      </div>

      {cur && avg ? (
        <div className="chart-note">
          익절까지 <b className="num">{toTarget == null ? '—' : '+' + toTarget.toFixed(2) + '%'}</b> 남음
          {' · '}현재 평가 <b className={'num ' + ((p.profit_pct ?? 0) >= 0 ? 'c-up' : 'c-down')}>{pct(p.profit_pct)}</b>
        </div>
      ) : (
        <div className="chart-note">보유 수량이 생기면 평단·익절선이 그려집니다.</div>
      )}

      {points.length < 2 && (
        <div className="chart-hint">데이터가 더 쌓이면 추이 선이 이어집니다. (현재 {points.length}일)</div>
      )}
    </div>
  )
}

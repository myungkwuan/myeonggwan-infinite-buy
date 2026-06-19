import { useRef } from 'react'

// viewBox 좌표계 (컨테이너 폭에 맞춰 스케일됨)
const W = 700, H = 360
const padL = 54, padR = 16, padT = 16, padB = 34
const plotW = W - padL - padR
const plotH = H - padT - padB

function niceTicks(min, max, count = 4) {
  if (min === max) return [min]
  const step = (max - min) / count
  const ticks = []
  for (let i = 0; i <= count; i++) ticks.push(min + step * i)
  return ticks
}

export default function SvgChart({ points, hoverIdx, onHover }) {
  const ref = useRef(null)
  const n = points.length

  // y 도메인: 가격/평단/익절(0·null 제외)
  const ys = []
  for (const p of points) {
    if (p.soxl_close) ys.push(p.soxl_close)
    if (p.avg_price_usd) ys.push(p.avg_price_usd)
    if (p.target_price) ys.push(p.target_price)
  }
  let yMin = Math.min(...ys), yMax = Math.max(...ys)
  if (!isFinite(yMin)) { yMin = 0; yMax = 1 }
  const padY = (yMax - yMin) * 0.08 || yMax * 0.05 || 1
  yMin -= padY; yMax += padY

  const xFor = (i) => (n <= 1 ? padL + plotW / 2 : padL + (i / (n - 1)) * plotW)
  const yFor = (v) => padT + (1 - (v - yMin) / (yMax - yMin)) * plotH

  const pathFor = (key) => {
    let d = '', started = false
    points.forEach((p, i) => {
      const v = p[key]
      if (!v) { started = false; return }
      d += (started ? ' L ' : ' M ') + xFor(i).toFixed(1) + ' ' + yFor(v).toFixed(1)
      started = true
    })
    return d
  }

  const ticks = niceTicks(yMin, yMax, 4)
  const dateLabel = (iso) => iso.slice(5).replace('-', '/')
  const labelIdx = n <= 1 ? [0] : [0, Math.floor((n - 1) / 2), n - 1].filter((v, i, a) => a.indexOf(v) === i)

  const handleMove = (e) => {
    const svg = ref.current
    if (!svg || n === 0) return
    const rect = svg.getBoundingClientRect()
    const x = ((e.clientX - rect.left) / rect.width) * W
    let i = n <= 1 ? 0 : Math.round(((x - padL) / plotW) * (n - 1))
    i = Math.max(0, Math.min(n - 1, i))
    onHover(i)
  }

  const hi = hoverIdx == null ? -1 : hoverIdx

  return (
    <svg
      ref={ref}
      className="chart-svg"
      viewBox={`0 0 ${W} ${H}`}
      preserveAspectRatio="xMidYMid meet"
      onPointerMove={handleMove}
      onPointerDown={handleMove}
      onPointerLeave={() => onHover(null)}
    >
      {/* 가로 그리드 + y 라벨 */}
      {ticks.map((t, i) => (
        <g key={i}>
          <line x1={padL} y1={yFor(t)} x2={W - padR} y2={yFor(t)} className="chart-grid" />
          <text x={padL - 8} y={yFor(t) + 4} textAnchor="end" className="chart-axis">
            ${t.toFixed(t < 10 ? 2 : 0)}
          </text>
        </g>
      ))}

      {/* x 날짜 라벨 */}
      {labelIdx.map((i) => (
        <text key={i} x={xFor(i)} y={H - 12} textAnchor="middle" className="chart-axis">
          {dateLabel(points[i].date)}
        </text>
      ))}

      {/* 라인: 익절(점선 초록) → 평단(골드) → 가격(흰) */}
      <path d={pathFor('target_price')} className="line-target" />
      <path d={pathFor('avg_price_usd')} className="line-avg" />
      <path d={pathFor('soxl_close')} className="line-price" />

      {/* 가격 점 */}
      {points.map((p, i) =>
        p.soxl_close ? (
          <circle key={'p' + i} cx={xFor(i)} cy={yFor(p.soxl_close)} r={i === hi ? 4.5 : 2.2}
                  className="dot-price" />
        ) : null
      )}

      {/* 매수/매도 마커 */}
      {points.map((p, i) => {
        const x = xFor(i)
        const y = p.soxl_close ? yFor(p.soxl_close) : null
        if (y == null) return null
        return (
          <g key={'m' + i}>
            {p.buy_qty > 0 && (
              <path d={`M ${x} ${y + 12} l -5 8 l 10 0 z`} className="mk-buy" />
            )}
            {p.sell_qty > 0 && (
              <path d={`M ${x} ${y - 12} l -5 -8 l 10 0 z`} className="mk-sell" />
            )}
          </g>
        )
      })}

      {/* 크로스헤어 */}
      {hi >= 0 && (
        <line x1={xFor(hi)} y1={padT} x2={xFor(hi)} y2={H - padB} className="chart-cross" />
      )}
    </svg>
  )
}

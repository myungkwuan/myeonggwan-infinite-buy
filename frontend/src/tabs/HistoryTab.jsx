import { useCallback, useEffect, useState } from 'react'
import { api } from '../api.js'
import { usd, krw, pct, modeEasy } from '../format.js'

const STATUS = {
  active: { label: '진행 중', cls: 'st-active' },
  completed: { label: '완료', cls: 'st-done' },
  quartered: { label: '쿼터 종료', cls: 'st-quarter' },
}

function modeCls(mode) {
  return mode === '후반전' ? 'jeon-h' : mode === '쿼터' ? 'jeon-q' : 'jeon-f'
}

function DayRow({ d }) {
  const profit = d.profit_pct
  return (
    <div className="hist-day">
      <div className="hd-top">
        <span className="hd-date num">{d.date.slice(5)}</span>
        <span className={'mode-dot ' + modeCls(d.mode)}>{modeEasy(d.mode)}</span>
        <span className="hd-t num">T{Number(d.turn_number).toFixed(1)}</span>
        <span className={'hd-pl num ' + ((profit ?? 0) >= 0 ? 'up' : 'down')}>{pct(profit)}</span>
      </div>
      <div className="hd-mid num">
        <span>평단 {d.avg_price_usd ? usd(d.avg_price_usd) : '—'}</span>
        <span>종가 {usd(d.soxl_close)}</span>
        {d.eval_value_krw != null && <span>평가 {krw(d.eval_value_krw)}</span>}
      </div>
      {d.fills && d.fills.length > 0 && (
        <div className="hd-fills">
          {d.fills.map((f, i) => (
            <span key={i} className={'fill ' + (f.action === 'buy' ? 'f-buy' : 'f-sell')}>
              {f.action === 'buy' ? '매수' : '매도'} {f.quantity}주 @{usd(f.price_usd)}
            </span>
          ))}
        </div>
      )}
    </div>
  )
}

function CycleCard({ s, onChanged }) {
  const [open, setOpen] = useState(false)
  const [days, setDays] = useState(null)
  const [busy, setBusy] = useState(false)
  const [err, setErr] = useState(null)
  const st = STATUS[s.status] || { label: s.status, cls: 'st-done' }
  const [reBusy, setReBusy] = useState(false)
  const [reErr, setReErr] = useState(null)

  const reopen = async () => {
    setReBusy(true); setReErr(null)
    try { await api.reopenSession(s.id); onChanged() }
    catch (e) { setReErr(e.message); setReBusy(false) }
  }

  const toggle = async () => {
    const next = !open
    setOpen(next)
    if (next && days == null) {
      setBusy(true); setErr(null)
      try {
        const list = await api.dailyList(s.id)
        setDays((list.points || []).slice().reverse())
      } catch (e) { setErr(e.message) }
      finally { setBusy(false) }
    }
  }

  return (
    <div className="cycle-card">
      <button className="cycle-hd" onClick={toggle}>
        <div className="ch-l">
          <div className="ch-title">사이클 <b>#{s.id}</b> <span className={'st ' + st.cls}>{st.label}</span></div>
          <div className="ch-sub num">
            {s.started_at ? s.started_at.slice(0, 10) : ''}{s.ended_at ? ' ~ ' + s.ended_at.slice(0, 10) : ' ~'}
          </div>
        </div>
        <div className="ch-r">
          {s.status === 'active' ? (
            <>
              <div className="num ch-main">T {Number(s.turn_number).toFixed(1)}/{s.divisions}</div>
              <div className="num ch-sub2">{s.holding_qty}주 · 평단 {s.avg_price_usd ? usd(s.avg_price_usd) : '—'}</div>
            </>
          ) : (
            <div className={'num ch-main ' + ((s.final_profit_pct ?? 0) >= 0 ? 'up' : 'down')}>
              {s.final_profit_pct != null ? pct(s.final_profit_pct) : '—'}
            </div>
          )}
          <span className={'caret' + (open ? ' open' : '')}>▾</span>
        </div>
      </button>

      {open && (
        <div className="cycle-body">
          {s.status !== 'active' && (
            <div className="reopen-box">
              <span>실수로 종료했나요?</span>
              <button className="reopen-btn" onClick={reopen} disabled={reBusy}>
                {reBusy ? '복구 중…' : '진행 중으로 되돌리기'}
              </button>
              {reErr && <div className="err">{reErr}</div>}
            </div>
          )}
          {busy && <div className="center sm"><div className="spin" /></div>}
          {err && <div className="err">{err}</div>}
          {days && days.length === 0 && <div className="empty">계산 이력이 없습니다.</div>}
          {days && days.map((d, i) => <DayRow key={i} d={d} />)}
        </div>
      )}
    </div>
  )
}

export default function HistoryTab() {
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [sessions, setSessions] = useState([])

  const load = useCallback(async () => {
    setLoading(true); setError(null)
    try {
      const h = await api.sessionHistory()
      setSessions(h.sessions || [])
    } catch (e) { setError(e.message) }
    finally { setLoading(false) }
  }, [])

  useEffect(() => { load() }, [load])

  if (loading) return <div className="center"><div className="spin" /></div>
  if (error) return <div className="error-card">{error}</div>
  if (sessions.length === 0)
    return <div className="center">아직 사이클이 없어요.<br />홈 탭에서 사이클을 시작하세요.</div>

  return (
    <div className="history">
      {sessions.map((s) => <CycleCard key={s.id} s={s} onChanged={load} />)}
    </div>
  )
}

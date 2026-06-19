import { useCallback, useEffect, useState } from 'react'
import { api } from '../api.js'
import { usd, krw, pct, qty } from '../format.js'
import { ModeBadge, ProgressBar, StatCard, Empty } from '../components/ui.jsx'
import OrderTicket from '../components/OrderTicket.jsx'
import ExecuteForm from '../components/ExecuteForm.jsx'
import ManualCalc from '../components/ManualCalc.jsx'
import TxManager from '../components/TxManager.jsx'

export default function HomeTab() {
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [session, setSession] = useState(null)
  const [daily, setDaily] = useState(null)
  const [config, setConfig] = useState(null)
  const [busy, setBusy] = useState(false)
  const [showExec, setShowExec] = useState(false)
  const [showClose, setShowClose] = useState(false)
  const [showTx, setShowTx] = useState(false)
  const [startTicker, setStartTicker] = useState('SOXL')

  const load = useCallback(async () => {
    setLoading(true); setError(null)
    try {
      const cur = await api.currentSession()
      const sess = cur.session
      if (!sess) {
        const cfg = await api.getConfig()
        setConfig(cfg); setSession(null); setDaily(null)
        setStartTicker(cfg.ticker || 'SOXL')
      } else {
        setSession(sess)
        const d = await api.calculate({})
        setDaily(d)
      }
    } catch (e) {
      setError(e.message)
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => { load() }, [load])

  const start = async () => {
    setBusy(true); setError(null)
    try { await api.startSession({ ticker: startTicker }); await load() }
    catch (e) { setError(e.message) }
    finally { setBusy(false) }
  }

  const recalc = async () => {
    setBusy(true); setError(null)
    try { setDaily(await api.calculate({})) }
    catch (e) { setError(e.message) }
    finally { setBusy(false) }
  }

  const doClose = async (status) => {
    setBusy(true); setError(null)
    try { await api.closeSession(session.id, status); setShowClose(false); await load() }
    catch (e) { setError(e.message) }
    finally { setBusy(false) }
  }

  if (loading) return <div className="center"><div className="spin" /></div>

  if (error) return (
    <div className="error-card">
      {error}
      <button className="btn btn-ghost" onClick={load}>다시 시도</button>
    </div>
  )

  // 활성 사이클 없음 → 시작 화면
  if (!session) return (
    <div className="start">
      <h2>새 사이클을 시작하세요</h2>
      <p>시작 시 환율을 자동조회해 회당 매수액을 고정합니다.</p>
      {config && (
        <div className="cfg">
          <div className="row"><span>종목</span><span>{config.ticker}</span></div>
          <div className="row"><span>시드</span><span className="num">{krw(config.seed_krw)}</span></div>
          <div className="row"><span>분할</span><span className="num">{config.divisions}분할</span></div>
          <div className="row"><span>익절 목표</span><span className="num">평단 +{config.target_pct}%</span></div>
          <div className="row"><span>환율 자동조회</span><span>{config.auto_rate ? '켜짐' : '꺼짐'}</span></div>
        </div>
      )}
      <div className="ticker-pick">
        {['SOXL', 'TQQQ'].map((t) => (
          <button key={t} className={'tk' + (startTicker === t ? ' on' : '')}
                  onClick={() => setStartTicker(t)}>{t}</button>
        ))}
      </div>
      {startTicker === 'TQQQ' && (
        <div className="tk-note">TQQQ는 보통 익절 +10%를 씁니다. 필요하면 ⚙ 설정에서 익절 목표를 바꾸세요.</div>
      )}
      <div className="actions">
        <button className="btn btn-gold" onClick={start} disabled={busy}>
          {busy ? '시작 중…' : startTicker + ' 사이클 시작'}
        </button>
      </div>
    </div>
  )

  // 활성 사이클 대시보드
  const ev = daily.evaluation
  const profitCls = ev.profit_pct >= 0 ? 'pos' : 'neg'
  const buys = daily.buy_orders || []
  const sells = daily.sell_orders || []

  return (
    <div>
      <div className="cycle-head">
        <div className="cyc">사이클 <b>#{session.id}</b> · {daily.date}</div>
        <ModeBadge mode={daily.mode} />
      </div>

      <ProgressBar value={daily.turn_number} max={session.divisions} />

      {daily.seed_alert && (
        <div className={'seed-alert ' + daily.seed_alert.level}>
          <span className="sa-icon">{daily.seed_alert.level === 'critical' ? '🔴' : '🟠'}</span>
          <span>{daily.seed_alert.message}</span>
        </div>
      )}

      <div className="grid2">
        <StatCard label="평단가" value={usd(daily.avg_price_usd)} sub={'현재가 ' + usd(daily.soxl_price)} />
        <StatCard label="보유 수량" value={qty(daily.holding_qty)} sub={'T ' + Number(daily.turn_number).toFixed(1) + ' 회차'} />
        <StatCard label="평가액" value={krw(ev.eval_value_krw)} sub={usd(ev.eval_value_usd)} />
        <StatCard label="평가손익" value={pct(ev.profit_pct)} sub={krw(ev.profit_krw)} cls={profitCls} />
      </div>

      <div className="rate-line">
        <span>적용 환율 <span className="num">₩{Math.round(daily.usd_krw_rate).toLocaleString('ko-KR')}</span> / $1</span>
        <span>회당 <span className="num">{usd(session.per_turn_usd)}</span></span>
      </div>

      <ManualCalc
        defaultRate={daily.usd_krw_rate}
        defaultPrice={daily.soxl_price}
        onResult={setDaily}
      />

      {daily.warnings && daily.warnings.map((w, i) => (
        <div className="note-warn" key={i}>⚠ {w}</div>
      ))}

      <div className="section">
        <div className="section-title">오늘 매수</div>
        {buys.length ? buys.map((o, i) => <OrderTicket key={i} order={o} kind="buy" />)
                     : <Empty text="오늘 매수 주문 없음 (쿼터 구간)" />}
      </div>

      <div className="section">
        <div className="section-title">오늘 매도</div>
        {sells.length ? sells.map((o, i) => <OrderTicket key={i} order={o} kind="sell" />)
                      : <Empty text="보유 수량이 없어 매도 주문 없음" />}
      </div>

      <div className="actions">
        <button className="btn btn-ghost" onClick={recalc} disabled={busy}>재계산</button>
        <button className="btn btn-gold" onClick={() => setShowExec(true)}>체결 입력</button>
      </div>

      {showExec && (
        <ExecuteForm
          daily={daily}
          onClose={() => setShowExec(false)}
          onDone={async () => { setShowExec(false); await recalc() }}
        />
      )}

      <button className="tx-link" onClick={() => setShowTx(true)}>체결 내역 보기·수정</button>

      {showTx && (
        <TxManager onClose={() => setShowTx(false)} onChanged={recalc} />
      )}

      {!showClose ? (
        <button className="close-link" onClick={() => setShowClose(true)}>사이클 종료…</button>
      ) : (
        <div className="close-box">
          <div className="close-msg">이 사이클을 종료할까요? 지금까지의 체결 기준으로 최종 수익이 기록됩니다.</div>
          <div className="close-actions">
            <button className="btn btn-ghost" onClick={() => doClose('completed')} disabled={busy}>익절 완료</button>
            <button className="btn btn-ghost" onClick={() => doClose('quartered')} disabled={busy}>쿼터 종료</button>
            <button className="close-cancel" onClick={() => setShowClose(false)} disabled={busy}>취소</button>
          </div>
        </div>
      )}
    </div>
  )
}

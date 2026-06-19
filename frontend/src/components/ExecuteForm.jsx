import { useState } from 'react'
import { api } from '../api.js'

function fromDaily(daily) {
  const rows = []
  for (const o of daily.buy_orders || [])
    rows.push({ action: 'buy', quantity: String(o.quantity), price_usd: o.price_usd == null ? '' : String(o.price_usd), order_type: o.order_type })
  for (const o of daily.sell_orders || [])
    rows.push({ action: 'sell', quantity: String(o.quantity), price_usd: o.price_usd == null ? '' : String(o.price_usd), order_type: o.order_type })
  return rows
}

export default function ExecuteForm({ daily, onClose, onDone }) {
  const [rows, setRows] = useState(() => fromDaily(daily))
  const [busy, setBusy] = useState(false)
  const [err, setErr] = useState(null)

  const upd = (i, k, v) => setRows((rs) => rs.map((r, idx) => (idx === i ? { ...r, [k]: v } : r)))
  const add = () => setRows((rs) => [...rs, { action: 'buy', quantity: '', price_usd: '', order_type: 'LOC' }])
  const del = (i) => setRows((rs) => rs.filter((_, idx) => idx !== i))

  const submit = async () => {
    setErr(null)
    const fills = rows
      .filter((r) => r.quantity !== '' && r.price_usd !== '')
      .map((r) => ({
        action: r.action,
        quantity: Number(r.quantity),
        price_usd: Number(r.price_usd),
        order_type: r.order_type || null,
      }))
    if (!fills.length) { setErr('체결된 행의 수량·가격을 입력하세요.'); return }
    setBusy(true)
    try {
      await api.execute(fills)
      onDone()
    } catch (e) {
      setErr(e.message)
    } finally {
      setBusy(false)
    }
  }

  return (
    <div className="overlay" onClick={onClose}>
      <div className="sheet" onClick={(e) => e.stopPropagation()}>
        <h3>체결 입력</h3>
        <p className="hint">실제로 체결된 주문만 남기고 수량·가격을 맞춰주세요. 체결 안 된 행은 비우거나 지우면 됩니다.</p>

        <div className="exec-tools">
          <button className="lnk" onClick={() => setRows(fromDaily(daily))}>오늘 주문 다시 불러오기</button>
          <button className="lnk" onClick={add}>행 추가</button>
        </div>

        {rows.map((r, i) => (
          <div className="exec-row" key={i}>
            <select value={r.action} onChange={(e) => upd(i, 'action', e.target.value)}>
              <option value="buy">매수</option>
              <option value="sell">매도</option>
            </select>
            <input inputMode="numeric" placeholder="수량" value={r.quantity} onChange={(e) => upd(i, 'quantity', e.target.value)} />
            <input inputMode="decimal" placeholder="체결가 $" value={r.price_usd} onChange={(e) => upd(i, 'price_usd', e.target.value)} />
            <button className="del" onClick={() => del(i)} aria-label="삭제">×</button>
          </div>
        ))}

        {err && <div className="err">{err}</div>}

        <div className="actions">
          <button className="btn btn-ghost" onClick={onClose} disabled={busy}>취소</button>
          <button className="btn btn-gold" onClick={submit} disabled={busy}>{busy ? '저장 중…' : '체결 저장'}</button>
        </div>
      </div>
    </div>
  )
}

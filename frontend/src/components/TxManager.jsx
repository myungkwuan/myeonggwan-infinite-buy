import { useEffect, useState } from 'react'
import { api } from '../api.js'
import { usd } from '../format.js'

function Row({ tx, onChanged }) {
  const [edit, setEdit] = useState(false)
  const [action, setAction] = useState(tx.action)
  const [qty, setQty] = useState(String(tx.quantity))
  const [price, setPrice] = useState(String(tx.price_usd))
  const [date, setDate] = useState(tx.date || '')
  const [busy, setBusy] = useState(false)
  const [err, setErr] = useState(null)

  const save = async () => {
    setErr(null)
    if (Number(qty) <= 0 || Number(price) <= 0) { setErr('수량·가격은 0보다 커야 해요.'); return }
    setBusy(true)
    try {
      await api.updateTransaction(tx.id, {
        action, quantity: Number(qty), price_usd: Number(price), date: date || null,
      })
      setEdit(false)
      onChanged()
    } catch (e) { setErr(e.message) } finally { setBusy(false) }
  }

  const remove = async () => {
    setBusy(true); setErr(null)
    try { await api.deleteTransaction(tx.id); onChanged() }
    catch (e) { setErr(e.message); setBusy(false) }
  }

  if (!edit) {
    return (
      <div className="tx-row">
        <span className={'tx-tag ' + (tx.action === 'buy' ? 't-buy' : 't-sell')}>
          {tx.action === 'buy' ? '매수' : '매도'}
        </span>
        <span className="tx-info num">{tx.date?.slice(5)} · {tx.quantity}주 · 주당 {usd(tx.price_usd)}</span>
        <div className="tx-btns">
          <button className="tx-edit" onClick={() => setEdit(true)}>수정</button>
          <button className="tx-del" onClick={remove} disabled={busy}>삭제</button>
        </div>
        {err && <div className="err tx-err">{err}</div>}
      </div>
    )
  }

  return (
    <div className="tx-row editing">
      <div className="tx-edit-grid">
        <select value={action} onChange={(e) => setAction(e.target.value)}>
          <option value="buy">매수</option>
          <option value="sell">매도</option>
        </select>
        <input inputMode="numeric" value={qty} onChange={(e) => setQty(e.target.value)} placeholder="수량" />
        <input inputMode="decimal" value={price} onChange={(e) => setPrice(e.target.value)} placeholder="가격$" />
        <input type="date" value={date} onChange={(e) => setDate(e.target.value)} />
      </div>
      {err && <div className="err tx-err">{err}</div>}
      <div className="tx-edit-btns">
        <button className="tx-edit" onClick={() => setEdit(false)} disabled={busy}>취소</button>
        <button className="tx-save" onClick={save} disabled={busy}>{busy ? '…' : '저장'}</button>
      </div>
    </div>
  )
}

export default function TxManager({ onClose, onChanged }) {
  const [list, setList] = useState(null)
  const [err, setErr] = useState(null)

  const reload = async () => {
    setErr(null)
    try { setList((await api.listTransactions()).transactions || []) }
    catch (e) { setErr(e.message) }
  }
  useEffect(() => { reload() }, [])

  const changed = async () => { await reload(); onChanged() }

  return (
    <div className="overlay" onClick={onClose}>
      <div className="sheet" onClick={(e) => e.stopPropagation()}>
        <h3>체결 내역 관리</h3>
        <p className="hint">잘못 입력한 체결을 수정·삭제하면 평단·보유가 자동으로 다시 계산돼요.</p>
        {err && <div className="err">{err}</div>}
        {list == null && <div className="center sm"><div className="spin" /></div>}
        {list && list.length === 0 && <div className="empty">입력된 체결이 없어요.</div>}
        {list && list.map((tx) => <Row key={tx.id} tx={tx} onChanged={changed} />)}
        <div className="actions" style={{ marginTop: 12 }}>
          <button className="btn btn-gold" onClick={onClose}>닫기</button>
        </div>
      </div>
    </div>
  )
}

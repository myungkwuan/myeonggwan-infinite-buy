import { useState } from 'react'
import { api } from '../api.js'

export default function ManualCalc({ defaultRate, defaultPrice, onResult }) {
  const [price, setPrice] = useState(defaultPrice ? String(defaultPrice) : '')
  const [rate, setRate] = useState(defaultRate ? String(Math.round(defaultRate)) : '')
  const [busy, setBusy] = useState(false)
  const [err, setErr] = useState(null)

  const go = async () => {
    setErr(null)
    if (price === '') { setErr('SOXL 현재가를 입력하세요.'); return }
    const body = { soxl_price: Number(price) }
    if (rate !== '') body.usd_krw_rate = Number(rate)
    setBusy(true)
    try { onResult(await api.calculate(body)) }
    catch (e) { setErr(e.message) }
    finally { setBusy(false) }
  }

  return (
    <div className="manual">
      <div className="manual-title">시세·환율 직접 입력</div>
      <div className="manual-row">
        <label>SOXL $
          <input inputMode="decimal" value={price} placeholder="24.55"
                 onChange={(e) => setPrice(e.target.value)} />
        </label>
        <label>환율 ₩
          <input inputMode="numeric" value={rate} placeholder="1390"
                 onChange={(e) => setRate(e.target.value)} />
        </label>
        <button className="btn btn-gold sm" onClick={go} disabled={busy}>
          {busy ? '…' : '계산'}
        </button>
      </div>
      {err && <div className="err">{err}</div>}
    </div>
  )
}

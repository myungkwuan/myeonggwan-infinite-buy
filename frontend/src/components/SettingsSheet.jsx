import { useEffect, useState } from 'react'
import { api } from '../api.js'
import { usd } from '../format.js'

export default function SettingsSheet({ onClose }) {
  const [cfg, setCfg] = useState(null)
  const [busy, setBusy] = useState(false)
  const [err, setErr] = useState(null)
  const [saved, setSaved] = useState(false)
  const [test, setTest] = useState(null)
  const [testing, setTesting] = useState(false)
  const [backupMsg, setBackupMsg] = useState(null)
  const [importing, setImporting] = useState(false)

  useEffect(() => {
    (async () => {
      try { setCfg(await api.getConfig()) }
      catch (e) { setErr(e.message) }
    })()
  }, [])

  const upd = (k, v) => { setCfg((c) => ({ ...c, [k]: v })); setSaved(false) }

  const save = async () => {
    setErr(null)
    const seed = Number(cfg.seed_krw), div = Number(cfg.divisions)
    const tgt = Number(cfg.target_pct), rate = Number(cfg.usd_krw_rate)
    if (!(seed > 0)) return setErr('시드는 0보다 커야 해요.')
    if (!(div > 0)) return setErr('분할 수는 0보다 커야 해요.')
    if (!(tgt > 0)) return setErr('익절 목표는 0보다 커야 해요.')
    if (!(rate > 0)) return setErr('기본 환율은 0보다 커야 해요.')
    setBusy(true)
    try {
      const next = await api.updateConfig({
        ticker: cfg.ticker, seed_krw: seed, divisions: div,
        target_pct: tgt, usd_krw_rate: rate, auto_rate: !!cfg.auto_rate,
      })
      setCfg(next); setSaved(true)
    } catch (e) { setErr(e.message) } finally { setBusy(false) }
  }

  const runTest = async () => {
    setTesting(true); setTest(null)
    try { setTest(await api.marketCheck()) }
    catch (e) { setTest({ error: e.message }) } finally { setTesting(false) }
  }

  const doExport = async () => {
    setBackupMsg(null)
    try {
      const data = await api.exportBackup()
      const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' })
      const url = URL.createObjectURL(blob)
      const a = document.createElement('a')
      const ts = new Date().toISOString().slice(0, 10)
      a.href = url; a.download = `myeonggwan-backup-${ts}.json`
      document.body.appendChild(a); a.click(); a.remove()
      URL.revokeObjectURL(url)
      setBackupMsg('백업 파일을 내려받았어요.')
    } catch (e) { setBackupMsg('내보내기 실패: ' + e.message) }
  }

  const doImport = async (file) => {
    if (!file) return
    if (!window.confirm('기존 데이터가 모두 이 백업으로 교체됩니다. 계속할까요?')) return
    setImporting(true); setBackupMsg(null)
    try {
      const text = await file.text()
      const data = JSON.parse(text)
      const r = await api.importBackup(data)
      setBackupMsg(`복원 완료: 사이클 ${r.restored.sessions} · 체결 ${r.restored.transactions}`)
    } catch (e) { setBackupMsg('복원 실패: ' + e.message) }
    finally { setImporting(false) }
  }

  return (
    <div className="overlay" onClick={onClose}>
      <div className="sheet" onClick={(e) => e.stopPropagation()}>
        <h3>설정</h3>
        {!cfg ? (
          <div className="center sm"><div className="spin" /></div>
        ) : (
          <>
            <div className="set-row toggle-row">
              <div>
                <div className="set-label">환율 자동조회</div>
                <div className="set-help">끄면 아래 기본 환율을 사용해요</div>
              </div>
              <button
                className={'toggle' + (cfg.auto_rate ? ' on' : '')}
                onClick={() => upd('auto_rate', !cfg.auto_rate)}
                aria-label="환율 자동조회 토글"
              ><span /></button>
            </div>

            <div className="set-row">
              <div className="set-label">기본 환율 (₩/$)</div>
              <input className="num" inputMode="decimal" value={cfg.usd_krw_rate}
                     onChange={(e) => upd('usd_krw_rate', e.target.value)} />
            </div>

            <div className="set-divider">아래는 <b>새 사이클부터</b> 적용</div>

            <div className="set-row">
              <div className="set-label">종목</div>
              <select className="set-select" value={cfg.ticker} onChange={(e) => upd('ticker', e.target.value)}>
                <option value="SOXL">SOXL</option>
                <option value="TQQQ">TQQQ</option>
              </select>
            </div>
            <div className="set-row">
              <div className="set-label">시드 (원)</div>
              <input className="num" inputMode="numeric" value={cfg.seed_krw}
                     onChange={(e) => upd('seed_krw', e.target.value)} />
            </div>
            <div className="set-row">
              <div className="set-label">분할 수</div>
              <input className="num" inputMode="numeric" value={cfg.divisions}
                     onChange={(e) => upd('divisions', e.target.value)} />
            </div>
            <div className="set-row">
              <div className="set-label">익절 목표 (%)</div>
              <input className="num" inputMode="decimal" value={cfg.target_pct}
                     onChange={(e) => upd('target_pct', e.target.value)} />
            </div>

            {err && <div className="err">{err}</div>}
            {saved && <div className="set-saved">저장됐어요. (새 사이클부터 반영)</div>}

            <div className="actions" style={{ marginTop: 12 }}>
              <button className="btn btn-ghost" onClick={onClose} disabled={busy}>닫기</button>
              <button className="btn btn-gold" onClick={save} disabled={busy}>{busy ? '저장 중…' : '저장'}</button>
            </div>

            <button className="set-test-btn" onClick={runTest} disabled={testing}>
              {testing ? '조회 중…' : '지금 환율·시세 조회 테스트'}
            </button>
            <div className="set-divider">데이터 백업</div>
            <div className="backup-row">
              <button className="btn btn-ghost" onClick={doExport}>내보내기</button>
              <label className="btn btn-ghost file-btn">
                {importing ? '복원 중…' : '가져오기'}
                <input type="file" accept="application/json,.json"
                       onChange={(e) => doImport(e.target.files[0])} disabled={importing} hidden />
              </label>
            </div>
            {backupMsg && <div className="set-saved">{backupMsg}</div>}

            {test && (
              <div className="set-test">
                {test.error ? <div className="err">{test.error}</div> : (
                  <>
                    <div className={test.fx?.ok ? 'ok' : 'bad'}>
                      환율: {test.fx?.ok ? `₩${Math.round(test.fx.value).toLocaleString('ko-KR')} (${test.fx.source})` : `실패 — ${test.fx?.error}`}
                    </div>
                    <div className={test.price?.ok ? 'ok' : 'bad'}>
                      SOXL: {test.price?.ok ? `${usd(test.price.value)} (${test.price.source})` : `실패 — ${test.price?.error}`}
                    </div>
                  </>
                )}
              </div>
            )}
          </>
        )}
      </div>
    </div>
  )
}

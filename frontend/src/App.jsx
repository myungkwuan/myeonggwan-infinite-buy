import { useEffect, useState } from 'react'
import { api } from './api.js'
import HomeTab from './tabs/HomeTab.jsx'
import ChartTab from './tabs/ChartTab.jsx'
import HistoryTab from './tabs/HistoryTab.jsx'
import StatsTab from './tabs/StatsTab.jsx'
import GuideTab from './tabs/GuideTab.jsx'
import SettingsSheet from './components/SettingsSheet.jsx'

const TABS = [
  { id: 'home', icon: '🏠', label: '홈' },
  { id: 'chart', icon: '📈', label: '차트' },
  { id: 'history', icon: '📜', label: '이력' },
  { id: 'stats', icon: '📊', label: '통계' },
  { id: 'guide', icon: '❓', label: '가이드' },
]

export default function App() {
  const [tab, setTab] = useState('home')
  const [showSettings, setShowSettings] = useState(false)
  const [ticker, setTicker] = useState('SOXL')

  useEffect(() => {
    (async () => {
      try {
        const cur = await api.currentSession()
        if (cur.session) { setTicker(cur.session.ticker); return }
        const cfg = await api.getConfig()
        setTicker(cfg.ticker)
      } catch (_) { /* 무시 */ }
    })()
  }, [tab, showSettings])
  const current = TABS.find((t) => t.id === tab)
  return (
    <div className="app">
      <header className="appbar">
        <div className="wordmark">명관 <b>무한매수법</b></div>
        <div className="appbar-r">
          <span className="ver">{ticker} · v2.2</span>
          <button className="gear" onClick={() => setShowSettings(true)} aria-label="설정">⚙</button>
        </div>
      </header>
      <main className="main">
        {tab === 'home' && <HomeTab />}
        {tab === 'chart' && <ChartTab />}
        {tab === 'history' && <HistoryTab />}
        {tab === 'stats' && <StatsTab />}
        {tab === 'guide' && <GuideTab />}
      </main>
      <nav className="tabbar">
        {TABS.map((t) => (
          <button key={t.id} className={tab === t.id ? 'active' : ''} onClick={() => setTab(t.id)}>
            <span className="ti">{t.icon}</span>
            <span className="tl">{t.label}</span>
          </button>
        ))}
      </nav>

      {showSettings && <SettingsSheet onClose={() => setShowSettings(false)} />}
    </div>
  )
}

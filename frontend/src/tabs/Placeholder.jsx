export default function Placeholder({ tab }) {
  return (
    <div className="placeholder">
      <div className="ph-icon">{tab.icon}</div>
      <div className="ph-title">{tab.label}</div>
      <div className="ph-sub">곧 만들 예정이에요</div>
    </div>
  )
}

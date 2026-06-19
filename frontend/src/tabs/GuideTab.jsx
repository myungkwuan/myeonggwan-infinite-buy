import { useState } from 'react'

function Section({ id, title, open, onToggle, children }) {
  return (
    <div className="guide-sec">
      <button className="guide-hd" onClick={() => onToggle(id)}>
        <span>{title}</span>
        <span className={'caret' + (open ? ' open' : '')}>▾</span>
      </button>
      {open && <div className="guide-body">{children}</div>}
    </div>
  )
}

export default function GuideTab() {
  const [open, setOpen] = useState('intro')
  const toggle = (id) => setOpen((cur) => (cur === id ? null : id))

  return (
    <div className="guide">
      <div className="guide-lead">
        이 앱은 <b>주문을 대신 넣어주지 않아요.</b> 라오어 무한매수법 v2.2대로
        “오늘 몇 주를 얼마에 사고팔지”를 계산해 줍니다. 그 숫자대로 유안타에서 직접 주문하세요.
      </div>

      <Section id="intro" title="① 한눈에 · 매일 루틴" open={open === 'intro'} onToggle={toggle}>
        <p>시드 5억을 40번에 쪼개 매일 약 <b>$8,992</b>씩 사 모으고, 평단보다 <b>+20%</b> 오르면 팔고 사이클을 끝냅니다.</p>
        <div className="g-steps">
          <div><b>1. 아침</b><span>홈 탭 열기 → 오늘 주문 자동 계산</span></div>
          <div><b>2. 주문</b><span>유안타에 그 가격·수량으로 주문 입력</span></div>
          <div><b>3. 밤(마감 후)</b><span>체결된 것만 “체결 입력”</span></div>
        </div>
        <div className="g-warn">체결 입력을 해야 평단·보유·진행단계(T)가 올라갑니다. 안 하면 계속 1일차 주문만 떠요.</div>
      </Section>

      <Section id="terms" title="② 핵심 용어" open={open === 'terms'} onToggle={toggle}>
        <table className="g-tbl">
          <tbody>
            <tr><td><b>진행단계(T)</b></td><td>누적 매수액 ÷ 회당. 40이면 시드 다 씀</td></tr>
            <tr><td><span className="m m-f">모으기</span></td><td>T 0~19 · 적극 매수 (하루 2건)</td></tr>
            <tr><td><span className="m m-q">쉬기</span></td><td>T 19~20 · 매수 쉼 (전환 구간)</td></tr>
            <tr><td><span className="m m-h">버티기</span></td><td>T 20~40 · 떨어질 때만 매수 (1건)</td></tr>
          </tbody>
        </table>
        <p className="g-note">단계 전환은 자동입니다. T가 오르면 모으기→쉬기→버티기로 알아서 바뀌어요.</p>
      </Section>

      <Section id="orders" title="③ 주문 종류 (유안타 매핑)" open={open === 'orders'} onToggle={toggle}>
        <table className="g-tbl">
          <tbody>
            <tr><td><b>LOC</b></td><td>마감가(종가)가 내 가격보다 유리하면 체결. 무한매수법 주력</td></tr>
            <tr><td><b>MOC</b></td><td>종가에 무조건 매도 (쉬기 구간 1/4)</td></tr>
            <tr><td><b>지정가</b></td><td>정한 가격 닿으면. 익절(+20%)에 사용</td></tr>
          </tbody>
        </table>
        <p className="g-note">유안타 = <b>특화주문</b> 메뉴에 LOC/MOC 있음. LOC/MOC는 <b>정규장 종료 20분 전까지</b> 입력. 넣고 주문내역 꼭 확인.</p>
      </Section>

      <Section id="buy" title="④ 매수 읽는 법" open={open === 'buy'} onToggle={toggle}>
        <p>“<b>16주 · 주당 $279.29</b>” = 한 주 $279.29에 16주 매수. 그 가격으로 <b>LOC 매수</b>를 거세요.</p>
        <p>종가가 그 가격보다 <b>싸게 끝나면 체결</b>, 비싸면 미체결(안 삼).</p>
        <div className="g-cards">
          <div><b>모으기</b><span>평단가에 매수 + 조금 비싸도 매수 (2건)</span></div>
          <div><b>버티기</b><span>많이 빠지면 매수 (1건)</span></div>
          <div><b>쉬기</b><span>매수 없음</span></div>
        </div>
      </Section>

      <Section id="sell" title="⑤ 매도 읽는 법" open={open === 'sell'} onToggle={toggle}>
        <p>보유가 있으면 매일 매도 <b>2건</b>이 같이 떠요 — 물량을 1/4 + 3/4로 쪼갬.</p>
        <table className="g-tbl">
          <tbody>
            <tr><td><b>일부 매도 1/4</b></td><td>단계별 가격. 쉬기 구간만 MOC(종가 매도)</td></tr>
            <tr><td><b>익절 3/4</b></td><td>평단 +20% 지정가 (항상 동일)</td></tr>
          </tbody>
        </table>
        <p className="g-note">버티기 구간에선 1/4 매도가가 <b>평단보다 낮게(−%)</b> 나올 수 있어요. 손실이어도 일부 팔아 자금 확보하는 전략이라 정상입니다.</p>
        <div className="g-warn g-ok">SOXL이 <b>평단 +20%</b> 닿으면 3/4 익절 체결 → 그 사이클 종료 신호. 체결 입력 후 홈에서 “사이클 종료”를 누르세요.</div>
      </Section>

      <Section id="cycle" title="⑥ 사이클 시작 ~ 종료" open={open === 'cycle'} onToggle={toggle}>
        <div className="g-flow">
          <div>사이클 시작 <span>환율 자동조회 · 회당 $8,992 고정</span></div>
          <div>매일 매수 쌓기 <span>주문 → 체결 입력 반복</span></div>
          <div>+20% 도달 → 익절 <span>3/4 매도 체결</span></div>
          <div>사이클 종료 <span>최종 수익 기록 → 통계·이력 반영</span></div>
          <div>새 사이클 시작 <span>반복</span></div>
        </div>
      </Section>

      <Section id="faq" title="⑦ 자주 막히는 것" open={open === 'faq'} onToggle={toggle}>
        <table className="g-tbl">
          <tbody>
            <tr><td><b>주문이 안 바뀌어요</b></td><td>체결 입력을 안 해서 T가 그대로. 매일 밤 체결분 입력</td></tr>
            <tr><td><b>자동조회 실패</b></td><td>홈의 “시세·환율 직접 입력”에 종가 넣고 계산</td></tr>
            <tr><td><b>수량이 회당과 안 맞아요</b></td><td>예산 내 정수 내림이라 몇 달러 오차 정상</td></tr>
            <tr><td><b>매도가 안 떠요</b></td><td>보유 0주면 매도 없음. 매수 체결되면 나옴</td></tr>
            <tr><td><b>LOC가 미체결</b></td><td>종가가 불리했던 것. 그날 그 주문만 체결 입력에서 빼면 됨</td></tr>
          </tbody>
        </table>
      </Section>

      <div className="guide-foot">수동 매매 보조 도구 · 실제 주문/체결은 직접 · 증권사 자동연동 없음</div>
    </div>
  )
}

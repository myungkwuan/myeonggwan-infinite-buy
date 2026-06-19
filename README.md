# 명관 무한매수법 (MyeonggwanInfinite)

라오어 미국주식 무한매수법 v2.2를 SOXL에 적용해 매일 LOC 주문 가격을
자동 계산해주는 웹앱. 수동 매매(키움 글로벌) 보조용 — 프로그램은 가격만 계산.

## 스택
- Backend: FastAPI (Python 3.11) · SQLAlchemy · PostgreSQL → Railway
- Frontend: React + Vite → Vercel  (Phase 2)
- 모바일 우선 / 다크 테마

## 개발 단계
- [x] Phase 0 (1) 폴더 구조 + 백엔드 골격
- [x] Phase 0 (2) v2.2 로직 함수 (calc_turn / calc_buy_orders / calc_sell_orders) + 환율/시세 유틸
- [x] Phase 0 (3) 단위 테스트 (18 passed)
- [x] Phase 1 API 엔드포인트 (session/daily/config, 21 passed)
- [x] Phase 2 (1) 프론트 스캐폴드 + 홈 탭 (빌드 OK)
- [x] Phase 2 (2) 차트 탭 (SVG 평단·가격·익절선 + 마커 + 크로스헤어)
- [x] Phase 2 (3) 이력 탭 (사이클별 아코디언 + 일별/체결)
- [x] Phase 2 (4) 통계 탭 (요약 + 사이클 수익 막대) + 사이클 종료
- [x] Phase 2 완료 — 4개 탭 전부 동작
- [x] 가이드 탭(❓) 추가 — 용어·주문·루틴 종합 설명
- [ ] Phase 3 배포

## 로컬 실행 (backend)
```powershell
cd backend
py -3.11 -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
copy .env.example .env
uvicorn app.main:app --reload
```
열기: http://127.0.0.1:8000/  ·  문서: http://127.0.0.1:8000/docs


## 로컬 실행 (frontend)
```powershell
cd frontend
npm install
copy .env.example .env     # VITE_API_BASE=http://127.0.0.1:8000
npm run dev
```
열기: http://127.0.0.1:5173  (백엔드 uvicorn도 같이 켜져 있어야 함)

- [x] 안정성 1단계 — 체결 수정/삭제 + 입력 검증
- [x] 안정성 2단계 — 설정 화면(⚙️): 환율 자동조회 토글·기본환율·시드·분할·익절 + 조회 테스트
- [x] 안정성 3단계 — 사이클 종료 되돌리기(reopen)
- [x] 안정성 4단계 — 쿼터 손절(T≈40) 알림 배너
- [x] 안정성 5단계 — 데이터 백업/복원 (JSON 내보내기·가져오기)
- [x] 6단계 — 종목 선택 (SOXL/TQQQ) · TQQQ 확장

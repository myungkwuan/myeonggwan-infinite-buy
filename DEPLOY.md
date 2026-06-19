# 배포 가이드 (모노레포)

구조: GitHub(myungkwuan/myeonggwan-infinite-buy) → Railway(backend+PostgreSQL) → Vercel(frontend)

## 1. GitHub 푸시
GitHub에서 빈 저장소 `myeonggwan-infinite-buy` 생성(README 체크 해제) 후:
```powershell
cd C:\Users\SEPC\Desktop\myeonggwan-infinite-buy ; git init ; git add . ; git commit -m "init: 명관 무한매수법"
cd C:\Users\SEPC\Desktop\myeonggwan-infinite-buy ; git branch -M main ; git remote add origin https://github.com/myungkwuan/myeonggwan-infinite-buy.git ; git push -u origin main
```

## 2. Railway (백엔드 + DB)
1. railway.app → New Project → Deploy from GitHub repo → 이 저장소 선택
2. 생성된 서비스 → Settings → **Root Directory = `backend`**
3. 프로젝트에 **New → Database → PostgreSQL** 추가 (Jang DB와 별개 프로젝트 권장)
4. 백엔드 서비스 → Variables 에서 PostgreSQL의 `DATABASE_URL` 연결 (Railway가 자동 주입되면 그대로)
5. 배포 후 도메인 생성: Settings → Networking → **Generate Domain** → `https://xxxx.up.railway.app`
6. 확인: `https://xxxx.up.railway.app/health` → `{"status":"healthy"}`

## 3. Vercel (프론트엔드)
1. vercel.com → Add New Project → 같은 GitHub 저장소 import
2. **Root Directory = `frontend`** (Framework: Vite 자동감지)
3. Environment Variables: `VITE_API_BASE = https://xxxx.up.railway.app` (2번 Railway 도메인)
4. Deploy → `https://yyyy.vercel.app`

## 4. CORS 연결
Railway 백엔드 Variables에 추가:
```
CORS_ORIGINS = https://yyyy.vercel.app
```
저장 시 자동 재배포. 이후 아이폰에서 `https://yyyy.vercel.app` 접속 → 홈 화면에 추가하면 앱처럼 사용.

## 메모
- 첫 기동 시 테이블 자동 생성(create_all). 운영 스키마 변경은 추후 Alembic.
- 데이터 백업: 앱 ⚙ → 데이터 백업 → 내보내기 (정기적으로).

FROM python:3.11-slim

WORKDIR /app

# 의존성 먼저 설치 (레이어 캐시)
COPY backend/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir --upgrade pip && pip install --no-cache-dir -r requirements.txt

# 백엔드 소스 복사 (app/ 등)
COPY backend/ ./

# Railway가 주입하는 $PORT 사용
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]

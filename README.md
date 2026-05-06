# StockBacktest — 보다영어

키움증권 조건검색식이 만족된 시점부터 N일 안에 목표 수익률에 도달하는 확률을 통계적으로 분석하는 시스템.

## 구성

```
StockBacktest/
├── backend/        # FastAPI (Python 3.11)
├── frontend/       # Next.js 16 + React 19 + Tailwind v4
├── src/            # 데이터 다운로드/조건식 (재사용 코드)
└── data/           # 일봉 CSV / SQLite / 신호 (gitignore)
```

## 로컬 개발

### 1. Python 가상환경 + 데이터 받기
```powershell
.\venv\Scripts\python.exe -m pip install -r requirements.txt
.\venv\Scripts\python.exe src\download_data.py all
.\venv\Scripts\python.exe src\test_signals.py
```

### 2. 백엔드
```powershell
cd backend
..\venv\Scripts\python.exe -m uvicorn app.main:app --port 8000
# → http://localhost:8000/docs
```

### 3. 프론트엔드
```powershell
cd frontend
npm install
npm run dev
# → http://localhost:3000
```

## 데이터 범위

- 종목: 코스피 + 코스닥 시총 1,000억↑ 보통주 (~1,500개)
- 기간: 5년 일봉
- 조건식: 급등주 추격형, 갭상승 정배열형 (확장 가능)

## 배포

- 백엔드: Railway
- 프론트엔드: Vercel

## 페이지

- `/` — 날짜별 분석
- `/matrix` — 전체 매트릭스
- `/regime` — 장세별 비교
- `/detail` — 종목별 상세
- `/themes` — 테마/주도주 (수동 큐레이션, Phase 4 키움 연동 예정)

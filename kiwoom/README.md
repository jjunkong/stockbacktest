# 키움 OpenAPI+ 연동 (Phase 4)

키움 OpenAPI+는 32-bit OCX 컨트롤이라 **64-bit Python으로 직접 호출 불가**.
이 폴더는 32-bit Python 3.10 별도 환경으로 분리됩니다.

## 환경

- Python: 32-bit Python 3.10.11 (`C:\Python310-x86\python.exe`)
- venv: `kiwoom/venv32/`
- 라이브러리: `pykiwoom`, `PyQt5`, `pandas==2.0.3`, `pywin32`

## 사전 조건 (사용자)

1. **키움증권 OpenAPI+ 사용 신청** 완료
2. **OpenAPI+ 설치** 완료 (보통 `C:\OpenAPI\`)
3. 모의투자 또는 실거래 계정

## 실행

### 로그인 테스트 (첫 단추)
```powershell
.\kiwoom\venv32\Scripts\python.exe kiwoom\login_test.py
```
키움 로그인 창이 뜸 → ID/PW 입력 → 계좌 정보 출력

### 조건검색 자동 실행
```powershell
.\kiwoom\venv32\Scripts\python.exe kiwoom\condition_runner.py
```
- 영웅문에서 미리 만든 조건검색식 자동 실행
- 결과: `data/kiwoom_signals/<날짜>.json`
- ⚠️ `CONDITION_NAME_MAP`에 영웅문 조건식 이름 → cond_id 매핑 필요

### 종목 PER/PBR/시총 수집
```powershell
.\kiwoom\venv32\Scripts\python.exe kiwoom\stock_info.py
.\kiwoom\venv32\Scripts\python.exe kiwoom\stock_info.py 50    # 상위 50종목만 테스트
```
- 결과: `data/fundamentals.json`
- 1,543종목 약 7분 소요

### 테마군 동기화
```powershell
.\kiwoom\venv32\Scripts\python.exe kiwoom\theme_collector.py
```
- 결과: `data/themes.json` (수동 큐레이션 덮어씀)

## 주의사항

- **TR 호출 제한**: 1초 5회 / 1분 100회 / 1시간 1000회. 코드에서 sleep 잘 줘야
- **로그인 창은 GUI**: 자동화 시 `pythonw` 대신 `python`으로 실행해야 창 보임
- **세션 유지**: pykiwoom의 Kiwoom 인스턴스는 프로세스가 살아있는 동안만 유효

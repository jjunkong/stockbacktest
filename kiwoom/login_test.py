"""
키움 OpenAPI+ 로그인 테스트.

OpenAPI+ 사용 신청 + 설치 + 승인 후 실행 가능.

실행:
    .\kiwoom\venv32\Scripts\python.exe kiwoom\login_test.py

흐름:
  1. Kiwoom() 인스턴스 → 키움 ActiveX 로드
  2. CommConnect() → 키움 로그인 창이 뜸 (사용자가 직접 ID/PW 입력)
  3. 로그인 성공 시 계좌번호, 사용자ID, 사용자명 등 출력
"""

from __future__ import annotations

import sys


def main() -> None:
    print("[1] PyQt5 + pykiwoom import...")
    try:
        from pykiwoom.kiwoom import Kiwoom
    except ImportError as e:
        print(f"[FAIL] pykiwoom import 실패: {e}")
        sys.exit(1)

    print("[2] Kiwoom 인스턴스 생성 (ActiveX 로드)...")
    try:
        kiwoom = Kiwoom()
    except Exception as e:
        print(f"[FAIL] ActiveX 로드 실패. 키움 OpenAPI+ 설치 확인 필요: {e}")
        print("       https://www3.kiwoom.com 에서 OpenAPI+ 다운로드")
        sys.exit(1)

    print("[3] CommConnect() 호출 → 키움 로그인 창 뜸. 직접 ID/PW 입력하세요...")
    kiwoom.CommConnect(block=True)  # 로그인 완료까지 블록

    print("[4] 로그인 정보 조회")
    user_id   = kiwoom.GetLoginInfo("USER_ID")
    user_name = kiwoom.GetLoginInfo("USER_NAME")
    server    = kiwoom.GetLoginInfo("GetServerGubun")  # "1" = 모의, 그 외 실거래
    accounts  = kiwoom.GetLoginInfo("ACCNO")           # 계좌번호 ;-separated

    server_label = "모의투자" if server == "1" else "실거래"

    print()
    print("=" * 50)
    print(f"  로그인 성공!")
    print("=" * 50)
    print(f"  사용자 ID  : {user_id}")
    print(f"  사용자명   : {user_name}")
    print(f"  서버       : {server_label}")
    print(f"  계좌번호   : {accounts}")
    print("=" * 50)


if __name__ == "__main__":
    main()

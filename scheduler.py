"""
Automated Naver ETF Data Crawler Scheduler.

이 스크립트는 schedule 라이브러리를 사용하여 1분 간격으로 네이버 금융 ETF 실시간 시세 데이터를 수집하고
`data/` 폴더에 저장한 뒤, 설정에 따라 Git 커밋 및 GitHub 자동 업로드를 수행합니다.
"""

import sys
import time
import subprocess
from datetime import datetime
from typing import Optional
import schedule
from src.naver_etf_crawler import NaverETFCrawler

# Windows 콘솔 한글 및 이모지 출력 인코딩 설정
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")


def job(auto_push: bool = False) -> None:
    """
    1분마다 반복 실행되는 수집 작업 함수.

    Args:
        auto_push (bool): 데이터 저장 후 GitHub로 자동 커밋 & 푸시할지 여부 (기본값 False).
    """
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{now_str}] [START] 네이버 ETF 데이터 수집 시작...")

    try:
        crawler = NaverETFCrawler()
        timestamp_file, latest_file = crawler.save_to_csv()
        print(f"[{now_str}] [SUCCESS] 데이터 저장 완료: {latest_file.name}")

        # Git 자동 푸시 옵션 활성화 시 커밋 및 푸시 실행
        if auto_push:
            commit_msg = f"auto: Update Naver ETF data ({now_str})"
            subprocess.run(["git", "add", "data/naver_etf_latest.csv"], check=False)
            subprocess.run(["git", "commit", "-m", commit_msg], check=False)
            subprocess.run(["git", "push", "origin", "main"], check=False)
            print(f"[{now_str}] [PUSH] GitHub (sunjinmo798-eng/ETF_EDA) 자동 업로드 시도 완료!")

    except Exception as e:
        print(f"[{now_str}] [ERROR] 데이터 수집 및 업로드 실패: {e}")


def start_scheduler(interval_minutes: int = 1, auto_push: bool = False) -> None:
    """
    지정된 분 간격으로 스케줄러 루프를 구동합니다.

    Args:
        interval_minutes (int): 수집 주기 (분 단위). 기본값 1분.
        auto_push (bool): 자동 Git 푸시 여부.
    """
    print(f"[*] Naver ETF 수집 스케줄러 가동 시작... (주기: {interval_minutes}분마다)")
    
    # 최초 1회 즉시 실행
    job(auto_push=auto_push)

    # schedule 스케줄 등록
    schedule.every(interval_minutes).minutes.do(job, auto_push=auto_push)

    # 무한 루프 구동
    try:
        while True:
            schedule.run_pending()
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n[*] 사용자에 의해 스케줄러가 정지되었습니다.")


if __name__ == "__main__":
    # 10분마다 수집 실행
    start_scheduler(interval_minutes=10, auto_push=False)

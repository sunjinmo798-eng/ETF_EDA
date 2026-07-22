"""
Naver Finance ETF Web Crawler Module.

이 모듈은 네이버 금융 실시간 시가총액순 ETF API
(https://finance.naver.com/api/sise/etfItemList.nhn?etfType=0&targetColumn=market_sum&sortOrder=desc)
데이터를 수집하고 Pandas DataFrame으로 정제하여 CSV 파일로 저장합니다.
"""

import re
import json
from typing import Optional, Dict, Any, List, Tuple
from datetime import datetime
from pathlib import Path
import pandas as pd
import requests


class NaverETFCrawler:
    """
    네이버 금융 ETF 데이터를 크롤링하고 저장하는 클래스.

    Attributes:
        url (str): 네이버 금융 ETF 실시간 API 엔드포인트 URL.
        params (Dict[str, Any]): 시가총액 순 정렬을 위한 쿼리 파라미터.
        headers (Dict[str, str]): HTTP 요청 헤더.
    """

    def __init__(self, etf_type: int = 0, target_column: str = "market_sum", sort_order: str = "desc") -> None:
        """
        NaverETFCrawler 초기화 메서드.

        Args:
            etf_type (int): ETF 유형 구분 값 (기본값 0: 전체).
            target_column (str): 정렬 대상 컬럼명 (기본값 'market_sum': 시가총액).
            sort_order (str): 정렬 방식 (기본값 'desc': 내림차순).
        """
        self.url: str = "https://finance.naver.com/api/sise/etfItemList.nhn"
        self.params: Dict[str, Any] = {
            "etfType": etf_type,
            "targetColumn": target_column,
            "sortOrder": sort_order
        }
        self.headers: Dict[str, str] = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            )
        }

    def fetch_etf_data(self) -> pd.DataFrame:
        """
        네이버 금융 ETF API에서 시가총액순 전종목 시세 데이터를 수집합니다.

        JSONP 콜백 형태로 응답이 오더라도 정규식으로 안전하게 순수 JSON 데이터만 추출하여 파싱합니다.

        Returns:
            pd.DataFrame: 수집된 ETF 항목별 시세 및 지표 데이터프레임.

        Raises:
            requests.RequestException: 네이버 API 통신 실패 시 발생.
            ValueError: 응답 데이터 파싱 실패 시 발생.
        """
        # 네이버 ETF API 호출
        response = requests.get(self.url, params=self.params, headers=self.headers, timeout=10)
        response.raise_for_status()

        raw_text = response.text.strip()

        # JSONP 콜백 패턴(예: window.__jindo2_callback._1824({...})) 처리
        if raw_text.startswith("window.") or "_callback" in raw_text:
            match = re.search(r'\{.*\}', raw_text, re.DOTALL)
            if match:
                raw_text = match.group(0)

        try:
            json_data = json.loads(raw_text)
            item_list: List[Dict[str, Any]] = json_data['result']['etfItemList']
        except (json.JSONDecodeError, KeyError) as e:
            raise ValueError(f"네이버 ETF API 데이터 파싱 중 오류 발생: {e}")

        # List[Dict] -> DataFrame 변환
        df = pd.DataFrame(item_list)

        # 주요 컬럼명 한글 매핑 및 정리
        rename_map = {
            'itemcode': '종목코드',
            'itemname': '종목명',
            'nowVal': '현재가',
            'changeVal': '전일대비',
            'changeRate': '등락률(%)',
            'nav': 'NAV',
            'threeMonthEarnRate': '3개월수익률(%)',
            'quant': '거래량',
            'amonut': '거래대금(백만)',
            'marketSum': '시가총액(억)'
        }
        df = df.rename(columns=rename_map)

        # 수집 시각 타임스탬프 컬럼 추가
        df['수집시각'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        return df

    def save_to_csv(self, output_dir: str = "data") -> Tuple[Path, Path]:
        """
        수집한 ETF 데이터를 최신 파일(naver_etf_latest.csv) 및 타임스탬프 이력 파일로 저장합니다.

        Args:
            output_dir (str): 저장할 대상 디렉토리 경로 (기본값 'data').

        Returns:
            Tuple[Path, Path]: (타임스탬프 이력 파일 경로, 최신 단일 파일 경로)

        Raises:
            OSError: 디렉토리 생성 또는 파일 작성 실패 시 발생.
        """
        df = self.fetch_etf_data()

        save_path = Path(output_dir)
        save_path.mkdir(parents=True, exist_ok=True)

        now_str = datetime.now().strftime("%Y%m%d_%H%M%S")
        timestamp_file = save_path / f"naver_etf_{now_str}.csv"
        latest_file = save_path / "naver_etf_latest.csv"

        # CSV 파일로 저장 (UTF-8-SIG 적용으로 엑셀 한글 깨짐 방지)
        df.to_csv(timestamp_file, index=False, encoding="utf-8-sig")
        df.to_csv(latest_file, index=False, encoding="utf-8-sig")

        return timestamp_file, latest_file


if __name__ == "__main__":
    crawler = NaverETFCrawler()
    t_file, l_file = crawler.save_to_csv()
    print(f"[*] 크롤링 완: {l_file}")

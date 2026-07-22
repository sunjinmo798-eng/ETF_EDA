"""
ETF Data Loader Module.

이 모듈은 yfinance API를 이용하여 지정된 ETF 종목 코드들의 
과거 주가 데이터 및 기본 메타정보를 수집하고 정전 처리(Data Cleansing)를 담당합니다.
"""

from typing import List, Dict, Any
import pandas as pd
import yfinance as yf


class ETFDataLoader:
    """
    ETF 데이터를 수집 및 관리하는 클래스.

    Attributes:
        tickers (List[str]): 수집 대상 ETF 티커 리스트.
    """

    def __init__(self, tickers: List[str]) -> None:
        """
        ETFDataLoader 초기화 메서드.

        Args:
            tickers (List[str]): 분석하고자 하는 ETF 티커 목록 (예: ['SPY', 'QQQ', 'IVV'])
        """
        self.tickers: List[str] = tickers

    def fetch_history(self, period: str = "1y", interval: str = "1d") -> pd.DataFrame:
        """
        지정한 기간과 주기에 해당하는 ETF의 종가(Close/Adj Close) 주가 데이터를 조회합니다.

        Args:
            period (str): 조회 기간 (예: '1mo', '6mo', '1y', '5y', 'max'). 기본값은 '1y'.
            interval (str): 데이터 주기 (예: '1d', '1wk', '1mo'). 기본값은 '1d'.

        Returns:
            pd.DataFrame: 각 ETF 티커를 컬럼으로 하고 날짜를 인덱스로 하는 종가 DataFrame.

        Raises:
            ValueError: 티커 리스트가 비어 있거나 데이터 로드 실패 시 발생.
        """
        if not self.tickers:
            raise ValueError("수집할 ETF 티커 리스트가 비어 있습니다.")

        # yfinance를 사용하여 시세 데이터 다운로드
        downloaded: pd.DataFrame = yf.download(
            tickers=self.tickers,
            period=period,
            interval=interval,
            progress=False
        )

        if downloaded.empty:
            raise ValueError("yfinance로부터 데이터를 불러오지 못했습니다.")

        # yfinance 최신 버전의 MultiIndex 구조 처리 ('Adj Close' 우선 사용, 없으면 'Close' 선택)
        if isinstance(downloaded.columns, pd.MultiIndex):
            price_type = 'Adj Close' if 'Adj Close' in downloaded.columns.levels[0] else 'Close'
            data = downloaded[price_type].copy()
        elif 'Adj Close' in downloaded.columns:
            data = downloaded['Adj Close'].copy()
        elif 'Close' in downloaded.columns:
            data = downloaded['Close'].copy()
        else:
            data = downloaded.copy()

        # 단일 티커 검색 시 Series가 반환될 경우 DataFrame으로 변환
        if isinstance(data, pd.Series):
            data = data.to_frame(name=self.tickers[0])

        # 결측치 보정 (선형 보간 및 전일 종가 대체)
        data = data.ffill().bfill()
        return data

    def fetch_info(self) -> Dict[str, Dict[str, Any]]:
        """
        각 ETF 티커의 요약 정보(운용자산, 수수료, 추종 지수 등)를 가져옵니다.

        Returns:
            Dict[str, Dict[str, Any]]: 티커별 정보 메타데이터 사전.
        """
        info_dict: Dict[str, Dict[str, Any]] = {}
        for ticker in self.tickers:
            yt = yf.Ticker(ticker)
            info_dict[ticker] = yt.info
        return info_dict

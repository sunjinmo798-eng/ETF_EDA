"""
ETF Exploratory Data Analysis (EDA) Analyzer Module.

이 모듈은 ETF 가격 데이터를 바탕으로 수익률, 연율화 변동성, 샤프 지수, MDD(Maximum Drawdown),
상관관계 등 금융 핵심 통계 지표를 계산하고 분석하는 기능을 제공합니다.
"""

from typing import Dict, Tuple
import numpy as np
import pandas as pd


class ETFAnalyzer:
    """
    ETF 데이터를 분석하고 주요 투자 평가지표를 계산하는 분석 클래스.
    """

    def __init__(self, price_df: pd.DataFrame, risk_free_rate: float = 0.035) -> None:
        """
        ETFAnalyzer 초기화 메서드.

        Args:
            price_df (pd.DataFrame): 일별 수정종가 가격 데이터 (Index: Datetime, Columns: Tickers).
            risk_free_rate (float): 무위험 이자율 (연율화 기본값 3.5%).
        """
        self.price_df: pd.DataFrame = price_df
        self.risk_free_rate: float = risk_free_rate
        # 일간 수익률 계산
        self.daily_returns: pd.DataFrame = price_df.pct_change().dropna()

    def get_cumulative_returns(self) -> pd.DataFrame:
        """
        누적 수익률(Cumulative Returns)을 계산합니다.

        Returns:
            pd.DataFrame: 각 ETF별 시점 기준 누적 수익률 DataFrame.
        """
        # (1 + R_1) * (1 + R_2) * ... - 1 계산을 수행하여 누적 수익률 측정
        return (1 + self.daily_returns).cumprod() - 1

    def calculate_performance_metrics(self, trading_days: int = 252) -> pd.DataFrame:
        """
        주요 성과 지표(연율화 수익률, 연율화 변동성, 샤프 지수, MDD)를 산출합니다.

        Args:
            trading_days (int): 연간 거래일 수 (기본값 252일).

        Returns:
            pd.DataFrame: 지표명(Index)과 티커별(Columns) 성과 요약 테이블.
        """
        # 1. 연율화 수익률 (Annualized Return)
        mean_daily_return = self.daily_returns.mean()
        annualized_return = mean_daily_return * trading_days

        # 2. 연율화 변동성 (Annualized Volatility)
        annualized_volatility = self.daily_returns.std() * np.sqrt(trading_days)

        # 3. 샤프 지수 (Sharpe Ratio)
        sharpe_ratio = (annualized_return - self.risk_free_rate) / annualized_volatility

        # 4. 최대 낙폭 (MDD: Maximum Drawdown)
        mdd = self._calculate_mdd()

        metrics_df = pd.DataFrame({
            "Annualized Return": annualized_return,
            "Annualized Volatility": annualized_volatility,
            "Sharpe Ratio": sharpe_ratio,
            "Max Drawdown (MDD)": mdd
        }).T

        return metrics_df

    def _calculate_mdd(self) -> pd.Series:
        """
        각 ETF의 최대 낙폭(Maximum Drawdown)을 계산하는 내부 메서드.

        Returns:
            pd.Series: 티커별 MDD 값 (음수 비율).
        """
        mdd_dict: Dict[str, float] = {}
        cumulative_prices = self.price_df / self.price_df.iloc[0]
        
        for col in cumulative_prices.columns:
            series = cumulative_prices[col]
            # 최고가(Peak) 추적
            running_max = series.cummax()
            # 고점 대비 낙폭(Drawdown) 계산
            drawdown = (series - running_max) / running_max
            mdd_dict[col] = float(drawdown.min())

        return pd.Series(mdd_dict)

    def get_correlation_matrix(self) -> pd.DataFrame:
        """
        ETF 간 일간 수익률의 상관계수(Correlation) 행렬을 생성합니다.

        Returns:
            pd.DataFrame: 상관계수 행렬 DataFrame.
        """
        return self.daily_returns.corr()

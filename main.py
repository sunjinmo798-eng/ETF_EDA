"""
ETF Exploratory Data Analysis (EDA) Main Script.

이 스크립트는 주요 ETF(SPY, QQQ, SCHD, TLT) 데이터를 수집하고
수익률, 리스크, 상관관계 등의 EDA 지표를 분석하여 결과를 출력합니다.
"""

from typing import List
from src.data_loader import ETFDataLoader
from src.eda_analyzer import ETFAnalyzer


def main() -> None:
    """
    ETF EDA 메인 실행 함수.
    """
    # 1. 수집 대상 ETF 티커 설정
    target_tickers: List[str] = ["SPY", "QQQ", "SCHD", "TLT"]
    print(f"[*] ETF 데이터 수집 시작... 대상 티커: {target_tickers}")

    # 2. 데이터 로더 인스턴스 생성 및 최근 1년 데이터 수집
    loader = ETFDataLoader(tickers=target_tickers)
    try:
        price_df = loader.fetch_history(period="1y", interval="1d")
        print(f"[+] 데이터 수집 완료! 데이터 크기: {price_df.shape}")
    except Exception as e:
        print(f"[!] 데이터 수집 중 오류 발생: {e}")
        return

    # 3. EDA 분석기 생성 및 성과 지표 계산
    analyzer = ETFAnalyzer(price_df=price_df)
    metrics_df = analyzer.calculate_performance_metrics()
    
    print("\n================ ETF Performance Summary ================")
    print(metrics_df.round(4))

    print("\n================ ETF Correlation Matrix ================")
    corr_df = analyzer.get_correlation_matrix()
    print(corr_df.round(4))


if __name__ == "__main__":
    main()

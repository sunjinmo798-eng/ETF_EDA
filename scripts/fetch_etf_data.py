"""
Naver Finance ETF Data Fetcher Script for GitHub Pages Static Dashboard.

이 스크립트는 네이버 금융 ETF API에서 실시간 데이터를 수집하고
GitHub Pages 대시보드에서 불러올 정적 JSON 파일(docs/data/etf_latest.json)로 저장합니다.
"""

import json
import re
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List
import requests


def fetch_and_save_etf_json(output_path: str = "docs/data/etf_latest.json") -> None:
    """
    네이버 ETF API 데이터를 가져와 JSON 파일로 저장합니다.

    Args:
        output_path (str): 저장할 정적 JSON 파일 경로.
    """
    url = "https://finance.naver.com/api/sise/etfItemList.nhn"
    params = {
        "etfType": 0,
        "targetColumn": "market_sum",
        "sortOrder": "desc"
    }
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0.0.0 Safari/537.36"
        )
    }

    print("[*] Fetching ETF data from Naver Finance API...")
    response = requests.get(url, params=params, headers=headers, timeout=10)
    response.raise_for_status()

    raw_text = response.text.strip()
    if raw_text.startswith("window.") or "_callback" in raw_text:
        match = re.search(r'\{.*\}', raw_text, re.DOTALL)
        if match:
            raw_text = match.group(0)

    data = json.loads(raw_text)
    items: List[Dict[str, Any]] = data.get("result", {}).get("etfItemList", [])

    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)

    result_payload = {
        "updated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "total_count": len(items),
        "items": items
    }

    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(result_payload, f, ensure_ascii=False, indent=2)

    print(f"[+] Successfully saved {len(items)} ETF items to {output_file}")


if __name__ == "__main__":
    fetch_and_save_etf_json()

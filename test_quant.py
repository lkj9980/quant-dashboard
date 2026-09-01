import os
import csv
import pandas as pd
import yfinance as datetime_dummy # (yfinance가 설치되어 있다고 가정)
import yfinance as yf
from datetime import datetime

# ---------------------------------------------------------
# 1. 로그 기록 함수 (지시하신 대로 폴더 자동 생성 없이 깔끔하게 구성)
# ---------------------------------------------------------
def append_to_quant_log(current_time, ticker_values):
    csv_filename = "data/quant_log.csv"
    
    file_exists = os.path.isfile(csv_filename)
    print(f"[DEBUG] 파일 존재 여부: {file_exists}")
    
    with open(csv_filename, mode='a', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        if not file_exists:
            writer.writerow(["Date"] + list(ticker_values.keys()))
            
        row_data = [current_time] + list(ticker_values.values())
        writer.writerow(row_data)
        print(f"[DEBUG] 데이터 행 추가 완료: {row_data}")

# ---------------------------------------------------------
# 2. 변곡점 분석 함수
# ---------------------------------------------------------
def analyze_index_turning_points():
    csv_filename = "data/quant_log.csv"
    if not os.path.exists(csv_filename):
        return "아직 누적된 지수 데이터가 없습니다."
    
    df = pd.read_csv(csv_filename)
    if len(df) < 2:
        return "변곡점을 분석하기에 데이터가 아직 부족합니다 (2개 이상 필요)."
    
    latest = df.iloc[-1]
    prev = df.iloc[-2]
    
    signals = []
    for col in df.columns:
        if col == "Date":
            continue
        
        curr_val = latest[col]
        prev_val = prev[col]
        
        if pd.isna(curr_val) or pd.isna(prev_val):
            continue
            
        diff_pct = ((curr_val - prev_val) / prev_val) * 100
        
        if abs(diff_pct) >= 1.0:
            direction = " 급등 🚀" if diff_pct > 0 else " 급락 📉"
            signals.append(f"• [변곡점 포착] {col}: {curr_val:,.2f} ({diff_pct:+.2f}%){direction}")
            
    if not signals:
        return "• 현재 특이사항(±1% 이상 변동) 없이 안정적인 횡보/추세 구간입니다."
        
    return "\n".join(signals)

# ---------------------------------------------------------
# 3. 데이터 수집 함수
# ---------------------------------------------------------
def collect_market_data():
    tickers = {
        "코스피": "^KS11", "코스닥": "^KQ11", "코스피 200": "^KS200",
        "S&P 500": "^GSPC", "나스닥 종합": "^IXIC", "나스닥 100": "^NDX",
        "S&P 500 선물": "ES=F", "나스닥 100 선물": "NQ=F", "러셀 2000 선물": "RTY=F",
        "미국 국채 10년": "^TNX", "미국 국채 30년": "^TYX",
        "USD/KRW 환율": "KRW=X", "WTI 유가": "CL=F",
        "국제 금": "GC=F", "구리 선물": "HG=F",
        "VIX 변동성": "^VIX"
    }
    
    print("1. 실시간 시장 데이터 수집 중...")
    data_summary = []
    ticker_values = {}
    
    for name, symbol in tickers.items():
        try:
            ticker = yf.Ticker(symbol)
            price = ticker.fast_info['last_price']
            prev_close = ticker.fast_info['previous_close']
            change_pct = ((price - prev_close) / prev_close) * 100
            
            data_summary.append(f"• {name}: {price:,.2f} ({change_pct:+.2f}%)")
            ticker_values[name] = f"{price:.2f}"
        except Exception:
            data_summary.append(f"• {name}: 조회 실패")
            ticker_values[name] = None
            
    turning_point_text = analyze_index_turning_points()
    data_summary.insert(0, turning_point_text)
    
    return "\n".join(data_summary), ticker_values

# ---------------------------------------------------------
# 4. 메인 실행부 (테스트 코드)
# ---------------------------------------------------------
if __name__ == "__main__":
    print("=== 퀀트 대시보드 테스트 실행 ===")
    
    # 현재 시간 생성
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M")
    
    # 1. 수집과 분석 분리 호출
    raw_text, ticker_values = collect_market_data()
    
    # 2. CSV 저장 (백테스트용) - 파일경로 오타(quant_log2.csv) 수정 반영 완료
    append_to_quant_log(current_time, ticker_values)
    
    print("\n=== 수집된 리포트 결과 ===")
    print(raw_text)

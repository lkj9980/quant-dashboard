import yaml
import pandas as pd
import numpy as np
import yfinance as yf

def load_config():
    with open("backtest_config.yaml", "r", encoding="utf-8") as f:
        return yaml.safe_load(f)

def run_backtest():
    # 1. 설정 파일 로드
    config = load_config()
    
    log_file = config['paths']['log_file']
    init_cap = config['capital']['initial_capital']
    assets = config['assets']
    
    print("=" * 60)
    print(" 🚀 설정파일 기반 퀀트 백테스트 시뮬레이션 가동")
    print("=" * 60)
    
    # 2. 로그 파일드 불러오기
    try:
        df_log = pd.read_csv(log_file)
    except FileNotFoundError:
        print(f"[에러] 로그 파일('{log_file}')을 찾을 수 없습니다. 경로를 확인해주세요.")
        return

    df_log['Date'] = pd.to_datetime(df_log['Date']).dt.normalize()
    df_log = df_log.sort_values('Date').reset_index(drop=True)
    
    # 3. 기간 설정 (YAML에 지정되어 있으면 그에 따르고, 없으면 로그의 전체 기간 사용)
    start_date = config['period']['start_date'] or df_log['Date'].min().strftime('%Y-%m-%d')
    end_date = config['period']['end_date'] or df_log['Date'].max().strftime('%Y-%m-%d')
    
    print(📌 검증 기간: {start_date} ~ {end_date} | 초기 자산: {init_cap:,.0f}원)
    
    # 4. 야후 파이낸스에서 자산별 가격 데이터 수집
    tickers = [asset['ticker'] for asset in assets]
    print(f"📥 야후 파이낸스 가격 데이터 수집 중... ({tickers})")
    
    raw_data = yf.download(tickers, start=start_date, end=end_date, progress=False)['Close']
    if isinstance(raw_data, pd.Series):
        raw_data = raw_data.to_frame()
        
    # 일일 수익률 계산
    returns = raw_data.pct_change().fillna(0)
    
    # 5. 로그 비중 데이터와 가격 수익률 병합
    sim_df = pd.DataFrame(index=returns.index)
    sim_df = sim_df.join(df_log.set_index('Date'), how='left')
    sim_df = sim_df.ffill().fillna(0) # 시그널 공백은 직전 유지
    
    # 6. 포트폴리오 전체 일일 수익률 계산 (YAML 설정에 등록된 자산과 비중 컬럼 동적 매핑)
    portfolio_daily_return = 0
    for asset in assets:
        t_code = asset['ticker']
        w_col = asset['weight_column']
        
        if w_col in sim_df.columns and t_code in returns.columns:
            portfolio_daily_return += sim_df[w_col] * returns[t_code]
        else:
            print(f"[경고] 설정된 컬럼('{w_col}') 또는 티커('{t_code}')가 데이터에 존재하지 않습니다.")

    sim_df['Strategy_Return'] = portfolio_daily_return
    sim_df['Cumulative_Return'] = (1 + sim_df['Strategy_Return']).cumprod()
    sim_df['Portfolio_Value'] = init_cap * sim_df['Cumulative_Return']
    
    # 7. 성과 지표 산출 (누적 수익률, MDD, 승률)
    final_value = sim_df['Portfolio_Value'].iloc[-1]
    total_return = (final_value - init_cap) / init_cap * 100
    
    rolling_max = sim_df['Cumulative_Return'].cummax()
    drawdown = (sim_df['Cumulative_Return'] - rolling_max) / rolling_max
    mdd = drawdown.min()
    
    win_days = (sim_df['Strategy_Return'] > 0).sum()
    total_trading_days = (sim_df['Strategy_Return'] != 0).sum()
    win_rate = (win_days / total_trading_days * 100) if total_trading_days > 0 else 0
    
    # 8. 최종 결과 출력
    print("\n" + "=" * 25 + " [백테스트 성과 요약] " + "=" * 25)
    print(f"• 초기 자본금      : {init_cap:,.0f} 원")
    print(f"• 최종 평가금      : {final_value:,.0f} 원")
    print(f"• 총 누적 수익률   : {total_return:.2f}%")
    print(f"• Maximum Drawdown : {mdd * 100:.2f}%")
    print(f"• 일간 승률        : {win_rate:.2f}% ({win_days}승 / {total_trading_days}거래일)")
    print("=" * 66)
    
    # 결과를 CSV로도 백업 저장
    output_path = config['paths']['output_report']
    sim_df.to_csv(output_path, encoding='utf-8-sig')
    print(f"💾 상세 백테스트 시뮬레이션 결과 저장 완료: {output_path}")

if __name__ == "__main__":
    run_backtest()

import os
import yaml
import pandas as pd
import numpy as np
from datetime import datetime

def run_backtest_and_generate_report():
    print("=" * 60)
    print("🚀 [DEBUG] 백테스트 및 리포트 자동 생성 파이프라인 가동")
    print("=" * 60)

    # 1. 설정 파일 로드
    config_path = "data/backtest_config.yaml"
    if not os.path.exists(config_path):
        raise FileNotFoundError(f"설정 파일({config_path})을 찾을 수 없습니다.")
        
    with open(config_path, "r", encoding="utf-8") as f:
        config = yaml.safe_load(f)

    quant_log_path = config["paths"]["quant_log_file"]
    pred_path = config["paths"]["prediction_file"]
    
    # Updated paths for results and templates
    latest_result_path = config["paths"]["output_report"]
    template_path = config["paths"]["template_file"]
    
    initial_capital = config["capital"]["initial_capital"]
    fee = config["capital"]["transaction_fee"]
    slippage = config["capital"]["slippage"]

    # 2. 인풋 데이터 로드
    if not os.path.exists(quant_log_path) or not os.path.exists(pred_path):
        raise FileNotFoundError(f"인풋 데이터 파일({quant_log_path} 또는 {pred_path})이 존재하지 않습니다.")

    df_quant = pd.read_csv(quant_log_path)
    df_pred = pd.read_csv(pred_path)

    df_quant['Date'] = pd.to_datetime(df_quant['Date'], format="mixed")
    df_pred['Date'] = pd.to_datetime(df_pred['Date'], format="mixed")

    # 3. 데이터 병합 및 기간 필터링
    df_merged = pd.merge(df_quant, df_pred, on="Date", how="inner")
    df_merged = df_merged.sort_values("Date").reset_index(drop=True)

    start_date = config["period"].get("start_date")
    end_date = config["period"].get("end_date")

    if start_date:
        df_merged = df_merged[df_merged['Date'] >= pd.to_datetime(start_date)]
    if end_date:
        df_merged = df_merged[df_merged['Date'] <= pd.to_datetime(end_date)]

    if df_merged.empty:
        raise ValueError("백테스트를 수행할 수 있는 데이터 구간이 비어 있습니다. 기간 설정을 확인하세요.")

    # 4. 백테스트 시뮬레이션 계산
    df_result = df_merged.copy()
    target_col = "코스피" if "코스피" in df_result.columns else df_result.columns[1]

    df_result['Daily_Return'] = df_result[target_col].pct_change().fillna(0)
    df_result['Strategy_Return'] = df_result['Daily_Return'] - (fee + slippage)
    df_result['Portfolio_Value'] = initial_capital * (1 + df_result['Strategy_Return']).cumprod()
    
    final_portfolio_value = df_result['Portfolio_Value'].iloc[-1]
    total_return_pct = ((final_portfolio_value - initial_capital) / initial_capital) * 100
    
    rolling_max = df_result['Portfolio_Value'].cummax()
    drawdown = (df_result['Portfolio_Value'] - rolling_max) / rolling_max
    mdd_pct = drawdown.min() * 100

    # 5. 결과 CSV 저장 (results 폴더)
    os.makedirs("results", exist_ok=True)
    df_result.to_csv(latest_result_path, index=False, encoding="utf-8-sig")
    print(f"[DEBUG] 최신 백테스트 결과 CSV 저장 완료: {latest_result_path}")

    # 6. 외부 HTML 템플릿 읽기 및 변수 치환
    if not os.path.exists(template_path):
        raise FileNotFoundError(f"백테스트 HTML 템플릿 파일({template_path})을 찾을 수 없습니다.")

    with open(template_path, "r", encoding="utf-8") as tf:
        html_template = tf.read()

    # 동적 값 주입 (템플릿 내부의 플레이스홀더를 실제 값으로 교체)
    update_time_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    total_return_str = f"{total_return_pct:+.2f}%"
    final_capital_str = f"{final_portfolio_value:,.0f} 원"
    mdd_str = f"{mdd_pct:.2f}%"
    
    dates_list = list(df_result['Date'].dt.strftime('%Y-%m-%d'))
    values_list = list(df_result['Portfolio_Value'])

    html_content = html_template.replace("{{UPDATE_TIME}}", update_time_str)
    html_content = html_content.replace("{{TOTAL_RETURN}}", total_return_str)
    html_content = html_content.replace("{{FINAL_CAPITAL}}", final_capital_str)
    html_content = html_content.replace("{{MDD}}", mdd_str)
    html_content = html_content.replace("{{DATES_JSON}}", str(dates_list))
    html_content = html_content.replace("{{VALUES_JSON}}", str(values_list))

    # 7. history/backtest/ 폴더에 타임스탬프 기반 HTML 아카이브 저장
    timestamp = datetime.now().strftime("%Y-%m-%d_%H%M%S")
    history_html_dir = "history/backtest"
    os.makedirs(history_html_dir, exist_ok=True)
    history_html_path = os.path.join(history_html_dir, f"backtest_{timestamp}.html")

    with open(history_html_path, "w", encoding="utf-8") as f:
        f.write(html_content)
    print(f"[DEBUG] 백테스트 아카이브 HTML 생성 완료: {history_html_path}")

    # 8. 콘솔 성과 요약 출력
    print("=" * 60)
    print("📊 [백테스트 성과 요약]")
    print(f"• 테스트 기간       : {df_result['Date'].iloc[0].strftime('%Y-%m-%d')} ~ {df_result['Date'].iloc[-1].strftime('%Y-%m-%d')}")
    print(f"• 총 데이터 포인트  : {len(df_result)}개 행")
    print(f"• 초기 자본금       : {initial_capital:,.0f} 원")
    print(f"• 최종 자산 가치    : {final_portfolio_value:,.2f} 원")
    print(f"• 총 누적 수익률    : {total_return_pct:+.2f}%")
    print(f"• 최대 낙폭 (MDD)   : {mdd_pct:.2f}%")
    print("=" * 60)

if __name__ == "__main__":
    run_backtest_and_generate_report()

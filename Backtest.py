import os
import yaml
import pandas as pd
import numpy as np

def run_backtest():
    # 1. 설정 파일 로드
    config_path = "data/backtest_config.yaml"
    if not os.path.exists(config_path):
        raise FileNotFoundError(f"설정 파일({config_path})을 찾을 수 없습니다.")
        
    with open(config_path, "r", encoding="utf-8") as f:
        config = yaml.safe_load(f)

    quant_log_path = config["paths"]["quant_log_file"]
    pred_path = config["paths"]["prediction_file"]
    output_path = config["paths"]["output_report"]
    
    initial_capital = config["capital"]["initial_capital"]
    fee = config["capital"]["transaction_fee"]
    slippage = config["capital"]["slippage"]

    print("🚀 백테스트 시뮬레이션 가동 중...")

    # 2. 인풋 데이터 로드 (날짜 포맷 섞임 방지를 위해 format="mixed" 적용)
    if not os.path.exists(quant_log_path) or not os.path.exists(pred_path):
        raise FileNotFoundError(f"인풋 데이터 파일({quant_log_path} 또는 {pred_path})이 존재하지 않습니다.")

    df_quant = pd.read_csv(quant_log_path)
    df_pred = pd.read_csv(pred_path)

    # 날짜 컬럼 파싱 (날짜만 있든 시간이 추가되었든 혼재되어 있어도 에러 안 남)
    df_quant['Date'] = pd.to_datetime(df_quant['Date'], format="mixed")
    df_pred['Date'] = pd.to_datetime(df_pred['Date'], format="mixed")

    # 3. 데이터 병합 (지표 정답지 + AI 예측값)
    df_merged = pd.merge(df_quant, df_pred, on="Date", how="inner")
    df_merged = df_merged.sort_values("Date").reset_index(drop=True)

    # 기간 필터링 설정이 있는 경우 적용
    start_date = config["period"]["start_date"]
    end_date = config["period"]["end_date"]
    if start_date:
        df_merged = df_merged[df_merged['Date'] >= pd.to_datetime(start_date)]
    if end_date:
        df_merged = df_merged[df_merged['Date'] <= pd.to_datetime(end_date)]

    if df_merged.empty:
        raise ValueError("백테스트를 수행할 수 있는 데이터 구간이 비어 있습니다. 기간 설정을 확인하세요.")

    # ==========================================
    # 4. 백테스트 시뮬레이션 및 성과 평가 로직
    # ==========================================
    df_result = df_merged.copy()
    
    # [예시 시뮬레이션 로직 보완] 
    # 실제 전략 수익률 계산 로직이 들어갈 자리입니다. 여기서는 테스트 출력을 위해 임시로 등락률 기반 계산을 흉내 냅니다.
    # 예: 코스피 컬럼이 존재한다면 해당 변화율을 기반으로 전략 수익률 산출
    target_col = "코스피" if "코스피" in df_result.columns else df_result.columns[1]
    
    df_result['Daily_Return'] = df_result[target_col].pct_change().fillna(0)
    # 수수료 및 슬리피지 반영 흉내 (거래 발생 시 가정)
    df_result['Strategy_Return'] = df_result['Daily_Return'] - (fee + slippage)
    
    # 누적 자산 가치 계산
    df_result['Portfolio_Value'] = initial_capital * (1 + df_result['Strategy_Return']).cumprod()
    
    # 주요 성과 지표 계산
    final_portfolio_value = df_result['Portfolio_Value'].iloc[-1]
    total_return_pct = ((final_portfolio_value - initial_capital) / initial_capital) * 100
    
    # MDD (Maximum Drawdown) 계산
    rolling_max = df_result['Portfolio_Value'].cummax()
    drawdown = (df_result['Portfolio_Value'] - rolling_max) / rolling_max
    mdd_pct = drawdown.min() * 100

    # ==========================================
    # 5. 아웃풋 결과 저장 폴더 자동 생성 및 저장
    # ==========================================
    output_dir = os.path.dirname(output_path)
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir, exist_ok=True)
        print(f"[DEBUG] 출력 디렉토리 생성 완료: {output_dir}")

    df_result.to_csv(output_path, index=False, encoding="utf-8-sig")
    
    # ==========================================
    # 6. 결과 리포트 콘솔 출력 (가시성 확보)
    # ==========================================
    print("=" * 40)
    print("📊 [백테스트 시뮬레이션 성과 요약]")
    print("=" * 40)
    print(f"• 테스트 기간       : {df_result['Date'].iloc[0].strftime('%Y-%m-%d')} ~ {df_result['Date'].iloc[-1].strftime('%Y-%m-%d')}")
    print(f"• 총 데이터 포인트  : {len(df_result)}개 행")
    print(f"• 초기 자본금       : {initial_capital:,.0f} 원")
    print(f"• 최종 자산 가치    : {final_portfolio_value:,.2f} 원")
    print(f"• 총 누적 수익률    : {total_return_pct:+.2f}%")
    print(f"• 최대 낙폭 (MDD)   : {mdd_pct:.2f}%")
    print("=" * 40)
    print(f"✅ 백테스트 완료! 성과 평가 결과 저장 위치: {output_path}")

if __name__ == "__main__":
    run_backtest()

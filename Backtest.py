import os
import yaml
import pandas as pd
import numpy as np

def run_backtest():
    # 1. 설정 파일 로드
    config_path = "backtest_config.yaml"
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
        raise FileNotFoundError("인풋 데이터 파일(quant_log.csv 또는 backtest_data.csv)이 존재하지 않습니다.")

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
    # TODO: 본인의 전략에 맞는 수익률 계산 및 평가 로직을 여기에 구현하세요.
    # 예시로 데이터프레임을 그대로 결과용으로 복사합니다.
    df_result = df_merged.copy()
    
    # 예시 평가 지표 컬럼 추가 (실제 계산 로직으로 대체 필요)
    df_result['Portfolio_Value'] = initial_capital  # 임시 자산 가치
    df_result['Strategy_Return'] = 0.0             # 임시 전략 수익률

    # ==========================================
    # 5. 아웃풋 결과 저장 (results/ 폴더 자동 생성)
    # ==========================================
    output_dir = os.path.dirname(output_path)
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir)

    df_result.to_csv(output_path, index=False, encoding="utf-8-sig")
    print(f"✅ 백테스트 완료! 성과 평가 결과 저장 위치: {output_path}")

if __name__ == "__main__":
    run_backtest()

import os
import yaml
import pandas as pd
import numpy as np

def run_backtest():
    print("=" * 50)
    print("🚀 [DEBUG] 백테스트 프로세스 시작")
    print("=" * 50)

    # 1. 설정 파일 로드
    config_path = "data/backtest_config.yaml"
    print(f"[DEBUG] 1. 설정 파일 확인 중: {config_path}")
    if not os.path.exists(config_path):
        print(f"[ERROR] 설정 파일을 찾을 수 없습니다: {config_path}")
        raise FileNotFoundError(f"설정 파일({config_path})을 찾을 수 없습니다.")
        
    with open(config_path, "r", encoding="utf-8") as f:
        config = yaml.safe_load(f)
    print("[DEBUG] 설정 파일 로드 성공")

    quant_log_path = config["paths"]["quant_log_file"]
    pred_path = config["paths"]["prediction_file"]
    output_path = config["paths"]["output_report"]
    
    initial_capital = config["capital"]["initial_capital"]
    fee = config["capital"]["transaction_fee"]
    slippage = config["capital"]["slippage"]

    print(f"[DEBUG] - 지표 로그 파일 경로 : {quant_log_path}")
    print(f"[DEBUG] - 예측값 파일 경로   : {pred_path}")
    print(f"[DEBUG] - 결과 리포트 경로   : {output_path}")

    # 2. 인풋 데이터 로드
    print("[DEBUG] 2. 인풋 데이터 파일 존재 여부 확인 중...")
    if not os.path.exists(quant_log_path):
        print(f"[ERROR] quant_log 파일이 없습니다: {quant_log_path}")
        raise FileNotFoundError(f"인풋 데이터 파일이 존재하지 않습니다: {quant_log_path}")
    if not os.path.exists(pred_path):
        print(f"[ERROR] prediction 파일이 없습니다: {pred_path}")
        raise FileNotFoundError(f"인풋 데이터 파일이 존재하지 않습니다: {pred_path}")

    df_quant = pd.read_csv(quant_log_path)
    df_pred = pd.read_csv(pred_path)
    print(f"[DEBUG] - df_quant 로드 완료 (행 수: {len(df_quant)})")
    print(f"[DEBUG] - df_pred 로드 완료 (행 수: {len(df_pred)})")

    # 날짜 파싱
    print("[DEBUG] 3. 날짜 컬럼 파싱 및 데이터 병합 중...")
    df_quant['Date'] = pd.to_datetime(df_quant['Date'], format="mixed")
    df_pred['Date'] = pd.to_datetime(df_pred['Date'], format="mixed")

    df_merged = pd.merge(df_quant, df_pred, on="Date", how="inner")
    df_merged = df_merged.sort_values("Date").reset_index(drop=True)
    print(f"[DEBUG] - 병합된 데이터 행 수: {len(df_merged)}")

    # 4. 기간 필터링 (YAML 설정 파일 값 사용)
    start_date = config["period"].get("start_date")
    end_date = config["period"].get("end_date")
    print(f"[DEBUG] 4. 기간 필터 적용 [시작: {start_date} ~ 종료: {end_date}]")

    if start_date:
        df_merged = df_merged[df_merged['Date'] >= pd.to_datetime(start_date)]
    if end_date:
        df_merged = df_merged[df_merged['Date'] <= pd.to_datetime(end_date)]

    print(f"[DEBUG] - 기간 필터링 후 데이터 행 수: {len(df_merged)}")
    if df_merged.empty:
        print("[ERROR] 필터링된 데이터 구간이 비어 있습니다.")
        raise ValueError("백테스트를 수행할 수 있는 데이터 구간이 비어 있습니다. `backtest_config.yaml`의 기간 설정을 확인하세요.")

    # 5. 백테스트 시뮬레이션 및 성과 평가 로직
    print("[DEBUG] 5. 백테스트 시뮬레이션 계산 중...")
    df_result = df_merged.copy()
    
    target_col = "코스피" if "코스피" in df_result.columns else df_result.columns[1]
    print(f"[DEBUG] - 기준 타겟 컬럼 선정: {target_col}")

    df_result['Daily_Return'] = df_result[target_col].pct_change().fillna(0)
    df_result['Strategy_Return'] = df_result['Daily_Return'] - (fee + slippage)
    df_result['Portfolio_Value'] = initial_capital * (1 + df_result['Strategy_Return']).cumprod()
    
    final_portfolio_value = df_result['Portfolio_Value'].iloc[-1]
    total_return_pct = ((final_portfolio_value - initial_capital) / initial_capital) * 100
    
    rolling_max = df_result['Portfolio_Value'].cummax()
    drawdown = (df_result['Portfolio_Value'] - rolling_max) / rolling_max
    mdd_pct = drawdown.min() * 100
    print("[DEBUG] - 시뮬레이션 연산 완료")

    # 6. 아웃풋 결과 저장 (신규 파일 생성 모드 / 덮어쓰기)
    print("[DEBUG] 6. 결과 파일 저장 처리 중...")
    output_dir = os.path.dirname(output_path)
    
    if output_dir:
        if not os.path.exists(output_dir):
            os.makedirs(output_dir, exist_ok=True)
            print(f"[DEBUG] - 아웃풋 디렉토리 신규 생성 완료: {output_dir}")
        else:
            print(f"[DEBUG] - 아웃풋 디렉토리 이미 존재함: {output_dir}")

    # 어펜드(Append)가 아닌 완전한 신규 파일 작성(Overwrite) 모드로 저장
    df_result.to_csv(output_path, index=False, encoding="utf-8-sig")
    print(f"[DEBUG] - 신규 결과 파일 쓰기 완료: {output_path}")

    # 7. 결과 리포트 콘솔 출력
    print("=" * 50)
    print("📊 [백테스트 시뮬레이션 성과 요약]")
    print("=" * 50)
    print(f"• 테스트 기간       : {df_result['Date'].iloc[0].strftime('%Y-%m-%d')} ~ {df_result['Date'].iloc[-1].strftime('%Y-%m-%d')}")
    print(f"• 총 데이터 포인트  : {len(df_result)}개 행")
    print(f"• 초기 자본금       : {initial_capital:,.0f} 원")
    print(f"• 최종 자산 가치    : {final_portfolio_value:,.2f} 원")
    print(f"• 총 누적 수익률    : {total_return_pct:+.2f}%")
    print(f"• 최대 낙폭 (MDD)   : {mdd_pct:.2f}%")
    print("=" * 50)
    print(f"✅ 백테스트 완료! 성과 평가 결과 저장 위치: {output_path}")

if __name__ == "__main__":
    run_backtest()

import os
import google.generativeai as genai
from datetime import datetime

# 1. API 키 설정 (GitHub Secrets에서 가져옴)
genai.configure(api_key=os.environ["GEMINI_API_KEY"])

def get_ai_analysis():
    # 여기에 실제 데이터 수집 로직(yfinance 등)을 넣거나 
    # 간단히 Gemini에게 시황 분석을 요청합니다.
    # ------------------------------------------
    # 1. 시장 지표 자동 수집 (yfinance)
    # ------------------------------------------
    tickers = {
        "S&P 500": "^GSPC", "나스닥 종합": "^IXIC", "다우존스": "^DJI",
        "미국 국채 10년": "^TNX", "USD/KRW 환율": "KRW=X",
        "WTI 유가": "CL=F", "국제 금": "GC=F", "VIX 변동성": "^VIX"
    }
    
    print("1. 실시간 시장 데이터 수집 중...")
    data_summary = []
    for name, symbol in tickers.items():
        try:
            ticker = yf.Ticker(symbol)
            price = ticker.fast_info['last_price']
            prev_close = ticker.fast_info['previous_close']
            change_pct = ((price - prev_close) / prev_close) * 100
            data_summary.append(f"• {name}: {price:,.2f} ({change_pct:+.2f}%)")
        except Exception:
            data_summary.append(f"• {name}: 조회 실패")
    
    raw_text = "\n".join(data_summary)
    
    # ------------------------------------------
    # 2. Gemini AI 매크로 분석
    # ------------------------------------------
    print("2. Gemini AI 시장 분석 중...")
    genai.configure(api_key=GEMINI_API_KEY)
    model = genai.GenerativeModel('gemini-3.5-flash')
    
    prompt = f"""
    너는 20년 경력의 수석 퀀트 전략가다.
    아래 실시간 지표를 바탕으로 매크로 시황을 분석하고 계좌별 전략을 작성하라.
    정량적 시장 지표는 수집된 지표(yfinance)에서 참고해야 하고, 임의로 숫자를 지어낼 수 없으며,
    정성적 시황(글로벌 매크로 뉴스, 연준 발언, 인사이트 등)은 폭넓은 실시간 웹 검색을 통해 종합적으로 분석하여, 일반 계좌와 퇴직연금 계좌의 자산 배분 포트폴리오를 도출하라.
    
    [수집된 지표(yfinance)]
    {raw_text}
    
    # [계좌별 규제 룰]
    1. [Portfolio A] 일반 계좌 (7개 자산군 합계 100%): 
       - 코스피200 ETF(레버/인버스), 코스닥150 ETF(레버/인버스), 나스닥100 ETF(레버/인버스), 현금 관망
    2. [Portfolio B] 퇴직연금 DC/IRP 계좌 (합계 100%): 위험자산 최대 70% 
       - 위험자산(코스피/코스닥/나스닥 ETF) 총합 최대 70% 제한
       - 안전자산(미국채 30년 ETF + 대기 현금)
       - 레버리지/인버스 매매 원천 금지
    
    [출력 형식]
    1. 오늘 시장의 핵심 변곡점을 꿰뚫는 한 문장 인용구 (Blockquote)
    2. [실시간 주요 지표 현황판] (마크다운)
    3. 시장별 포지션 스코어링(0~100점): 매수/매도 비교 점수 (코스피200 / 코스닥150 / 나스닥100)
    4. Portfolio A (일반계좌) 추천 비중
    5. Portfolio B (퇴직연금 DC/IRP) 추천 비중 (위험자산 최대 70%)
    6. 분할 매수/매도 가격 타점 및 액션 플랜
    - 미사여구를 배제하고 모든 수치와 가격은 명확한 숫자로만 출력할 것.
    """
    
    response = model.generate_content(prompt)
    report_content = response.text
    return response.text

def generate_html(ai_comment, kospi, nasdaq, fx):
    current_time = datetime.now().strftime('%Y-%m-%d %H:%M')
    
    html_template = f"""<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Daily Quant Dashboard</title>
    <style>
        body {{ font-family: sans-serif; background-color: #f8f9fa; padding: 20px; }}
        .card {{ background: white; border-radius: 16px; padding: 20px; margin-bottom: 16px; box-shadow: 0 2px 8px rgba(0,0,0,0.1); }}
        h1 {{ font-size: 18px; }}
        .metric {{ display: flex; justify-content: space-between; padding: 10px 0; border-bottom: 1px solid #eee; }}
    </style>
</head>
<body>
    <div style="max-width: 480px; margin: auto;">
        <h1>계좌별 맞춤 포트폴리오 전략</h1>
        <div class="card">
            <h3>💡 매크로 변곡점</h3>
            <p>{ai_comment}</p>
        </div>
        <div class="card">
            <h3>📊 실시간 지표</h3>
            <div class="metric"><span>코스피</span><span>{kospi}</span></div>
            <div class="metric"><span>나스닥</span><span>{nasdaq}</span></div>
            <div class="metric"><span>환율</span><span>{fx}</span></div>
        </div>
        <p style="text-align:center; font-size:12px;">Last Updated: {current_time}</p>
    </div>
</body>
</html>"""
    with open('index.html', 'w', encoding='utf-8') as f:
        f.write(html_template)

# 실행부
if __name__ == "__main__":
    ai_text = get_ai_analysis()
    # 실제로는 여기서 yfinance 등으로 데이터를 가져와 변수에 넣어야 합니다.
    generate_html(ai_text, "2,600.00", "19,000.00", "1,380.00")

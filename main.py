import os
import yfinance as yf
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
    - 오직 Tailwind CSS 클래스를 사용한 순수 HTML <div> 카드 형태로만 출력하세요.
    - 전체 응답은 아래 카드 구조(div)를 포함해야 합니다:
       - 카드 1: 오늘의 매크로 변곡점 한 줄 요약(Blockquote) (class="bg-white rounded-2xl p-5 shadow-sm mb-4 border border-gray-100")
       - 카드 2. [실시간 주요 지표 현황판] (마크다운)
       - 카드 3: 시장별 포지션 스코어링 및 점수 (class="bg-white rounded-2xl p-5 shadow-sm mb-4 border border-gray-100")
       - 카드 4: Portfolio A (일반계좌) 추천 비중 (class="bg-white rounded-2xl p-5 shadow-sm mb-4 border border-gray-100")
       - 카드 5. Portfolio B (퇴직연금 DC/IRP) 추천 비중 (위험자산 최대 70%) (class="bg-white rounded-2xl p-5 shadow-sm mb-4 border border-gray-100")
       - 카드 6. 분할 매수/매도 가격 타점 및 액션 플랜
    """

    response = model.generate_content(prompt)
    report_content = response.text
    return response.text

def generate_html(ai_html_content):
    current_time = datetime.now().strftime('%Y-%m-%d %H:%M')
    
    html_template = f"""<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Daily Quant Dashboard</title>
    <!-- Tailwind CSS CDN -->
    <script src="https://cdn.tailwindcss.com"></script>
</head>
<body class="bg-slate-50 text-slate-800 p-4 max-w-xl mx-auto">
    
    <!-- 상단 타이틀 영역 -->
    <header class="mb-6 mt-2">
        <h1 class="text-2xl font-black tracking-tight text-slate-900">계좌별 맞춤 포트폴리오 전략</h1>
        <p class="text-xs text-slate-500 mt-1">최신 매크로 시황 및 실시간 퀀트 분석 결과</p>
    </header>

    <!-- AI가 생성한 카드 영역 -->
    <main>
        {ai_html_content}
    </main>

    <!-- 푸터 -->
    <footer class="text-center text-[11px] text-slate-400 mt-8 mb-4">
        Last Updated: {current_time} • Powered by GitHub Pages & Gemini AI
    </footer>
</body>
</html>"""
    with open('index.html', 'w', encoding='utf-8') as f:
        f.write(html_template)

# 실행부
if __name__ == "__main__":
    ai_text = get_ai_analysis()
    # 실제로는 여기서 yfinance 등으로 데이터를 가져와 변수에 넣어야 합니다.
    generate_html(ai_text)

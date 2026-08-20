import pandas as pd
import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from datetime import datetime
import markdown
import yfinance as yf
from google import genai
from datetime import datetime, timezone, timedelta
import csv

# 1. 데이터 수집 함수 (데이터를 딕셔너리로 반환)
def collect_market_data():
    # 여기에 실제 데이터 수집 로직(yfinance 등)을 넣거나 
    # 간단히 Gemini에게 시황 분석을 요청합니다.
    # ------------------------------------------
    # 1. 시장 지표 자동 수집 (yfinance)
    # ------------------------------------------
    tickers = {
        # 국내 지수
        "코스피": "^KS11", "코스닥": "^KQ11", "코스피 200": "^KS200",
        #"코스피 200 선물": "169=F", # 야후 파이낸스 코스피 200 선물 심볼
        # 해외 지수 & 선물
        "S&P 500": "^GSPC", "나스닥 종합": "^IXIC", "나스닥 100": "^NDX",
        "S&P 500 선물": "ES=F", "나스닥 100 선물": "NQ=F", "러셀 2000 선물": "RTY=F",
        # 금리 / 환율 / 원자재 / 변동성
        "미국 국채 10년": "^TNX", "미국 국채 30년": "^TYX",
        "USD/KRW 환율": "KRW=X", "WTI 유가": "CL=F",
        "국제 금": "GC=F", "구리 선물": "HG=F",
        "VIX 변동성": "^VIX"
    }
    
    print("1. 실시간 시장 데이터 수집 중...")
    data_summary = []
    ticker_values = {} # CSV 저장용 딕셔너리
    
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
            
    # --- 🎯 [핵심] 수집이 끝난 직후, 상단에 변곡점 분석 결과 밀어 넣기 ---
    turning_point_text = analyze_index_turning_points()
    
    # data_summary 리스트의 가장 맨 앞에 변곡점 문구 삽입
    data_summary.insert(0, turning_point_text)
    
    return "\n".join(data_summary), ticker_values

def analyze_index_turning_points():
    csv_filename = "history/quant_log.csv"
    if not os.path.exists(csv_filename):
        return "아직 누적된 지수 데이터가 없습니다."
    
    df = pd.read_csv(csv_filename)
    if len(df) < 2:
        return "변곡점을 분석하기에 데이터가 아직 부족합니다 (2개 이상 필요)."
    
    # 가장 최근 데이터와 직전 데이터 비교
    latest = df.iloc[-1]
    prev = df.iloc[-2]
    
    signals = []
    # CSV의 Date 컬럼을 제외한 지수 컬럼들만 순회
    for col in df.columns:
        if col == "Date":
            continue
        
        curr_val = latest[col]
        prev_val = prev[col]
        
        if pd.isna(curr_val) or pd.isna(prev_val):
            continue
            
        # 변동률 계산
        diff_pct = ((curr_val - prev_val) / prev_val) * 100
        
        # ±1% 이상 변동이 발생했을 때를 '변곡점'으로 감지
        if abs(diff_pct) >= 1.0:
            direction = " 급등 🚀" if diff_pct > 0 else " 급락 📉"
            signals.append(f"• [변곡점 포착] {col}: {curr_val:,.2f} ({diff_pct:+.2f}%){direction}")
            
    if not signals:
        return "• 현재 특이사항(±1% 이상 변동) 없이 안정적인 횡보/추세 구간입니다."
        
    return "\n".join(signals)

def append_to_quant_log(current_time, ticker_values):
    csv_filename = "history/quant_log.csv"
    file_exists = os.path.isfile(csv_filename)
    with open(csv_filename, mode='a', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        if not file_exists:
            writer.writerow(["Date"] + list(ticker_values.keys()))
        writer.writerow([current_time] + list(ticker_values.values()))

# 2. 분석 함수 (수집된 raw_text를 인자로 받음)
def get_ai_analysis(GEMINI_API_KEY, raw_text):
    # ------------------------------------------
    # 2. Gemini AI 매크로 분석
    # ------------------------------------------
    print("2. Gemini AI 시장 분석 중...")
    #genai.configure(api_key=GEMINI_API_KEY)
    #model = genai.GenerativeModel('gemini-3.5-flash')
    prompt = f"""
    너는 20년 경력의 수석 퀀트 전략가다. 아래 지표를 바탕으로 매크로 시황을 분석하고 계좌별 전략을 작성하라.
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
    - 마크다운 기호(###, **, |, - 등)를 절대 사용하지 마세요.
    - 오직 Tailwind CSS 클래스를 사용한 순수 HTML <div> 카드 형태로만 출력하세요.
    - 전체 응답은 아래 카드 구조(div)를 포함해야 합니다:
       - 카드 1: 오늘의 매크로 변곡점 한 줄 요약(Blockquote) (class="bg-white rounded-2xl p-5 shadow-sm mb-4 border border-gray-100")
       - 카드 2. [실시간 주요 지표 현황판] (마크다운)
       - 카드 3: 시장별 포지션 스코어링 및 점수 (class="bg-white rounded-2xl p-5 shadow-sm mb-4 border border-gray-100")
       - 카드 4: Portfolio A (일반계좌) 추천 비중 (class="bg-white rounded-2xl p-5 shadow-sm mb-4 border border-gray-100")
       - 카드 5. Portfolio B (퇴직연금 DC/IRP) 추천 비중 (위험자산 최대 70%) (class="bg-white rounded-2xl p-5 shadow-sm mb-4 border border-gray-100")
       - 카드 6. 분할 매수/매도 가격 타점 및 액션 플랜
    """
    # 클라이언트 초기화 (환경 변수 GEMINI_API_KEY가 설정되어 있다면 인자 생략 가능)
    client = genai.Client(api_key=GEMINI_API_KEY)
    
    response = client.models.generate_content(
        model="gemini-3.5-flash",
        contents=prompt,
    )

    #response = model.generate_content(prompt)
    return response.text

def generate_html(today_date, current_time, ai_html_content):
    # 1. 아카이브 폴더 생성
    os.makedirs("history", exist_ok=True)
    
    # 개별 일일 리포트 파일 경로
    daily_filename = f"history/{current_time}.html"
    
    # 공통 HTML 템플릿
    html_template = f"""<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Daily Quant Dashboard - {today_date}</title>
    <!-- Tailwind CSS -->
    <script src="https://cdn.tailwindcss.com"></script>
    <!-- Chart.js CDN -->
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
</head>
<body class="bg-slate-50 text-slate-800 p-4 max-w-xl mx-auto">
    
    <!-- 상단 타이틀 영역 -->
    <header class="mb-6 mt-2 flex justify-between items-center">
        <div>
            <h1 class="text-2xl font-black tracking-tight text-slate-900">계좌별 맞춤 포트폴리오 전략</h1>
            <p class="text-xs text-slate-500 mt-1">최신 매크로 시황 및 실시간 퀀트 분석 결과 ({today_date})</p>
        </div>
        <a href="../index.html" class="text-xs bg-slate-200 hover:bg-slate-300 px-3 py-1.5 rounded-lg font-bold transition">메인으로</a>
    </header>
    <!-- 메인 콘텐츠 영역 -->
    <main class="space-y-6">
        
        <!-- 2. CSV 트렌드 차트 영역 (AI 본문 바로 위에 배치) -->
        <section class="bg-white p-4 rounded-2xl shadow-sm border border-gray-100">
            <h2 class="text-sm font-bold text-slate-700 mb-3">📈 지수 ETF 실시간 트렌드</h2>
            <div class="relative w-full h-56">
                <canvas id="quantChart"></canvas>
            </div>
        </section>
        <!-- 화면에 진행 상황을 찍어줄 임시 디버그 박스 -->
        <div id="debug-view" style="background: #1e293b; color: #38bdf8; padding: 12px; margin: 10px 0; font-family: monospace; font-size: 11px; border-radius: 8px; white-space: pre-wrap;">디버그 대기 중...</div>

        <!-- 4. CSV를 읽어서 차트를 그려주는 자바스크립트 -->
        <script src="../chart.js"></script>
        
        <!-- 3. AI가 생성한 카드 영역 (본문) -->
        <div>
            {ai_html_content}
        </div>
        
    </main>

    <!-- 푸터 -->
    <footer class="text-center text-[11px] text-slate-400 mt-8 mb-4">
        Last Updated: {current_time} • Powered by GitHub Pages & Gemini AI
    </footer>
        
</body>
</html>"""
    
    # 오늘 날짜 파일로 아카이브 저장
    with open(daily_filename, 'w', encoding='utf-8') as f:
        f.write(html_template)

    # 2. history 폴더에 있는 모든 리포트 목록을 읽어서 메인 index.html의 아카이브 목록 구성
    files = sorted([f for f in os.listdir("history") if f.endswith(".html")], reverse=True)    
        
    archive_links = ""
    for file in files:
        date_str = file.replace(".html", "")
        archive_links += f"""
        <a href="history/{file}" class="block bg-white p-4 rounded-xl shadow-sm border border-gray-100 hover:border-blue-400 transition mb-3 flex justify-between items-center">
            <span class="font-bold text-slate-700">📅 {date_str} 일일 퀀트 리포트</span>
            <span class="text-xs text-blue-600 font-semibold">보기 &rarr;</span>
        </a>
        """

    # 메인 인덱스 페이지 (아카이브 허브 역할 + 오늘자 내용 병행 표시)
    index_template = f"""<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Daily Quant Dashboard - Hub</title>
    <script src="https://cdn.tailwindcss.com"></script>
</head>
<body class="bg-slate-50 text-slate-800 p-4 max-w-xl mx-auto">
    
    <header class="mb-6 mt-2">
        <h1 class="text-2xl font-black tracking-tight text-slate-900">퀀트 리포트 아카이브 허브</h1>
        <p class="text-xs text-slate-500 mt-1">날짜별 과거 시황 분석 및 트렌드 기록실</p>
    </header>

    <!-- 오늘자 바로가기 최상단 배치 -->
    <div class="mb-6">
        <a href="{daily_filename}" class="block bg-blue-600 text-white p-4 rounded-2xl shadow-md hover:bg-blue-700 transition font-bold text-center">
            🔥 오늘자 ({today_date}) 최신 리포트 보러가기
        </a>
    </div>

    <!-- 과거 히스토리 목록 -->
    <section>
        <h2 class="text-sm font-bold text-slate-400 uppercase tracking-wider mb-3">Previous Reports</h2>
        <div class="space-y-2">
            {archive_links}
        </div>
    </section>

    <footer class="text-center text-[11px] text-slate-400 mt-12 mb-4">
        Powered by GitHub Pages & Gemini AI
    </footer>
</body>
</html>"""

    # 메인 index.html 갱신
    with open('index.html', 'w', encoding='utf-8') as f:
        f.write(index_template)
        
    return index_template
    
def send_gmail_report(current_time, html_template, GMAIL_APP_PASSWORD,MY_EMAIL):
    # 3. 마크다운을 예쁜 HTML 웹페이지 코드로 변환
    html_body = markdown.markdown(html_template, extensions=['tables', 'fenced_code'])
    # 웹페이지 스타일 꾸미기 (보기 편한 디자인 템플릿)
    styled_html = f"""<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
<style>
  body {{ font-family: 'Apple SD Gothic Neo', 'Malgun Gothic', sans-serif; color: #333; line-height: 1.6; padding: 20px; background-color: #f9f9f9; }}
  .container {{ max-width: 700px; margin: 0 auto; background: #ffffff; padding: 30px; border-radius: 10px; box-shadow: 0 4px 10px rgba(0,0,0,0.05); }}
  h1, h2, h3 {{ color: #1a365d; }}
  blockquote {{ border-left: 4px solid #3182ce; margin: 20px 0; padding: 10px 20px; background: #ebf8ff; color: #2b6cb0; font-style: italic; }}
  table {{ width: 100%; border-collapse: collapse; margin: 20px 0; }}
  th, td {{ border: 1px solid #e2e8f0; padding: 10px 12px; text-align: left; font-size: 14px; }}
  th {{ background-color: #f7fafc; color: #4a5568; }}
  code, pre {{ background: #edf2f7; padding: 2px 6px; border-radius: 4px; font-family: monospace; font-size: 13px; }}
  pre {{ padding: 15px; white-space: pre-wrap; }}
</style>
</head>
<body>
<div class="container">
  {html_body}
</div>
</body>
</html>
"""
    
    # 4. Gmail 발송 (오늘 날짜 자동 적용)
    #today_date = datetime.now().strftime("%Y-%m-%d")
    
    msg = MIMEMultipart()
    msg['From'] = MY_EMAIL
    msg['To'] = MY_EMAIL
    msg['Subject'] = f"[일일 퀀트 리포트] {current_time} 시장 분석 및 자산 배분 전략"
    
    msg.attach(MIMEText(styled_html, 'html', 'utf-8'))
    
    server = smtplib.SMTP_SSL('smtp.gmail.com', 465)
    server.login(MY_EMAIL, GMAIL_APP_PASSWORD)
    server.sendmail(MY_EMAIL, MY_EMAIL, msg.as_string())
    server.close()
    print("Gmail HTML 리포트 발송 완료!")

# 실행부
if __name__ == "__main__":
    # 한국 시간(KST, UTC+9) 타임존 정의
    KST = timezone(timedelta(hours=9))
    
    # 기존 datetime.now() 대신 아래처럼 KST를 넣어줍니다.
    today_date = datetime.now(KST).strftime("%Y-%m-%d")
    current_time = datetime.now(KST).strftime('%Y-%m-%d %H:%M')
    
    GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
    
    # [수정] 1. 수집과 분석을 분리하여 호출
    raw_text, ticker_values = collect_market_data()
    
    # [추가] 2. CSV 저장 (백테스트용)
    append_to_quant_log(current_time, ticker_values)
    
    # [수정] 3. 분석 수행
    ai_text = get_ai_analysis(GEMINI_API_KEY, raw_text)
    
    # 4. HTML 생성
    html_template = generate_html(today_date, current_time, ai_text)
    
    #GMAIL_APP_PASSWORD = os.environ.get("GMAIL_APP_PASSWORD")    # gg내 메일 주소 설정 (보내는 사람과 받는 사람 동일)
    #MY_EMAIL = os.environ.get("MY_EMAIL")
    #send_gmail_report(current_time, html_template, GMAIL_APP_PASSWORD, MY_EMAIL)

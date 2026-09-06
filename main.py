# 1. 표준 라이브러리 (Python Built-in)
import csv
import json
import os
import re
import time
from datetime import datetime, timezone, timedelta
from collections import defaultdict

# 2. 서드파티 라이브러리 (External Packages)
import markdown
import pandas as pd
import yfinance as yf
from google import genai
from google.genai import types
from google.genai.errors import ServerError

# 3. 커스텀 모듈 (Local Modules)
#from backtest_schema import QuantBacktestData

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
    csv_filename = "data/quant_log.csv"
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
    csv_filename = "data/quant_log.csv"
    
    file_exists = os.path.isfile(csv_filename)
    #print(f"[DEBUG] 파일 존재 여부: {file_exists}")
    with open(csv_filename, mode='a', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        if not file_exists:
            writer.writerow(["Date"] + list(ticker_values.keys()))
        row_data = [current_time] + list(ticker_values.values())
        writer.writerow(row_data)
        #print(f"[DEBUG] 데이터 행 추가 완료: {row_data}")

def call_gemini_with_retry(client, model_name, prompt_text, max_retries=3, delay=5):
    for attempt in range(1, max_retries + 1):
        try:
            print(f"🔄 Gemini API 호출 시도 ({attempt}/{max_retries})...")
            response = client.models.generate_content(
                model=model_name,
                contents=prompt_text,
            )
            return response
        except ServerError as e:
            print(f"⚠️ 서버 과부하(503) 또는 일시적 오류 발생: {e}")
            if attempt == max_retries:
                print("❌ 최대 재시도 횟수 초과.")
                raise e
            wait_time = delay * attempt
            print(f"⏳ {wait_time}초 후 재시도합니다...")
            time.sleep(wait_time)
        except Exception as e:
            print(f"❌ 예상치 못한 에러 발생: {e}")
            raise e

# 2. 분석 함수 (수집된 raw_text를 인자로 받음)
def get_ai_analysis_and_backtest_data(GEMINI_API_KEY, raw_text):
    # ------------------------------------------
    # 2. Gemini AI 매크로 분석
    # ------------------------------------------
    print("2. Gemini AI 시장 분석 중...")
    
    #1. 백테스트 JSON 템플릿 읽기 및 오늘 날짜 주입
    with open("data/backtest_template.json", "r", encoding="utf-8") as f:
        backtest_json_snippet = f.read()

    #genai.configure(api_key=GEMINI_API_KEY)
    #model = genai.GenerativeModel('gemini-3.5-flash')

    # 2. 프롬프트 템플릿 읽기 및 raw_text와 백테스트 스니펫 주입
    with open("data/prompt_template.txt", "r", encoding="utf-8") as f:
        template_str = f.read()

    # 3. 최종 프롬프트 완료 
    prompt = template_str.format(raw_text=raw_text,backtest_json_snippet=backtest_json_snippet)

    # 클라이언트 초기화 (환경 변수 GEMINI_API_KEY가 설정되어 있다면 인자 생략 가능)
    client = genai.Client(api_key=GEMINI_API_KEY)
    response = call_gemini_with_retry(
        client=client,
        model_name="gemini-3.5-flash", # 또는 사용하시는 모델명
        prompt_text=prompt,
        max_retries=3,
        delay=30
    )
    #config=types.GenerateContentConfig(
    #        temperature=0.2,

    #response = model.generate_content(prompt)

    return response.text

def save_to_backtest_csv(ai_text, today_date):
    match = re.search(r'<script type="application/json" id="backtest-json">(.*?)</script>', ai_text, re.DOTALL)
    if not match: return
    
    data = json.loads(match.group(1).strip())
    
    row_data = {
        "Date": today_date,
        # Portfolio A (일반 계좌: 레버/인버스 6개 + 현금)
        "A_Kospi200_Lev": data["portfolio_a"]["kospi200_lev_weight"],
        "A_Kospi200_Inv": data["portfolio_a"]["kospi200_inv_weight"],
        "A_Kosdaq150_Lev": data["portfolio_a"]["kosdaq150_lev_weight"],
        "A_Kosdaq150_Inv": data["portfolio_a"]["kosdaq150_inv_weight"],
        "A_Nasdaq100_Lev": data["portfolio_a"]["nasdaq100_lev_weight"],
        "A_Nasdaq100_Inv": data["portfolio_a"]["nasdaq100_inv_weight"],
        "A_Cash": data["portfolio_a"]["cash_weight"],
        
        # Portfolio B (퇴직연금 DC/IRP: 위험자산 총합/안전자산 총합 + 상세 세부)
        "B_Kospi200": data["portfolio_b"]["kospi200_weight"],
        "B_Kosdaq150": data["portfolio_b"]["kosdaq150_weight"],
        "B_Nasdaq100": data["portfolio_b"]["nasdaq100_weight"],
        "B_US_Treasury_30Y": data["portfolio_b"]["us_treasury_30y_weight"],
        "B_DC_IRP_Cash": data["portfolio_b"]["dc_irp_cash_weight"],
    }
    
    df_new = pd.DataFrame([row_data])
    csv_file = "data/backtest_data.csv"
    
    try:
        #df_existing = pd.read_csv(csv_file)
        #df_existing = df_existing[df_existing['Date'] != today_date]
        #df_final = pd.concat([df_existing, df_new], ignore_index=True)
        if os.path.exists(csv_file):
            #print(f">> [디버그 5-1] 기존 파일 존재함. 읽기 시도...")
            df_existing = pd.read_csv(csv_file)
            #print(f">> [디버그 5-2] 기존 파일 읽기 성공 (행 개수: {len(df_existing)})")
            
            df_existing = df_existing[df_existing['Date'].astype(str) != str(today_date)]
            df_final = pd.concat([df_existing, df_new], ignore_index=True)
            #print(">> [디버그 5-3] 기존 데이터 + 신규 데이터 병합 완료")
        else:
            #print(">> [디버그 5-4] 기존 파일 없음. 새로 생성 모드")
            df_final = df_new
    except FileNotFoundError:
        #print(f">> [디버그 5 예외 발생] 파일 읽기/병합 중 에러: {e}")
        df_final = df_new

    df_final.to_csv(csv_file, index=False, encoding="utf-8-sig")
    print(f">> [백테스트 데이터 저장 성공] {today_date} 비중이 backtest_data.csv에 동기화되었습니다.")

def create_daily_report(today_date, current_time, ai_html_content):
    # 1. 아카이브 폴더 생성
    os.makedirs("history", exist_ok=True)
    
    # 개별 일일 리포트 파일 경로
    daily_filename = f"history/{current_time}.html"

    # 1. 외부 HTML 템플릿 파일 읽어오기
    template_path = "html/report_template.html"
    with open(template_path, "r", encoding="utf-8") as f:
        html_template = f.read()
        
    # 2. 동적 데이터(날짜 및 AI 본문 내용) 치환
    html_template = html_template.replace("{today_date}", today_date)
    html_template = html_template.replace("{ai_html_content}", ai_html_content)  # 이 부분 추가!
    html_template = html_template.replace("{current_time}", current_time)
    
    # 3. 오늘 날짜 아카이브 파일로 저장
    with open(daily_filename, 'w', encoding='utf-8') as f:
        f.write(html_template)

    return daily_filename

def get_badge_html(time_part):
    """외부 JSON 설정 파일을 로드하여 시간대에 따른 배지 HTML 반환"""
    # 기본값 설정
    selected_label = "정기발행"
    selected_class = "bg-slate-100 text-slate-600"
    
    try:
        hour = int(time_part.split(":")[0])
        
        # 외부 설정 파일 경로 (프로젝트 구조에 맞게 경로 수정 가능)
        config_path = "html/badges_config.json"
        
        if os.path.exists(config_path):
            with open(config_path, "r", encoding="utf-8") as f:
                badges = json.load(f)
                
            for badge in badges:
                if hour >= badge["threshold"]:
                    selected_label = badge["label"]
                    selected_class = badge["class"]
                    break
                    
    except (ValueError, IndexError, json.JSONDecodeError):
        pass

    return f'<span class="text-[10px] font-bold px-2 py-1 rounded-lg {selected_class}">{selected_label}</span>'
 
def build_archive_links():
    # 2. history 폴더에 있는 모든 리포트 목록을 읽어서 메인 index.html의 아카이브 목록 구성
    files = sorted([f for f in os.listdir("history") if f.endswith(".html")], reverse=True)
    
    # 1. 날짜별로 파일 그룹화 (예: {'2026-09-03': ['2026-09-03 15:55.html', ...], ...})
    grouped_files = defaultdict(list)
    for file in sorted(files, reverse=True):
        filename_core = file.replace(".html", "")
        if " " in filename_core:
            date_part, time_part = filename_core.split(" ")
        else:
            date_part = filename_core # 날짜만 있는 구형 파일 포맷 대응
        grouped_files[date_part].append(file)
        
    # 아카이브 개별 아이템용 외부 템플릿 읽기
    item_template_path = "html/archive_item_template.html"
    with open(item_template_path, "r", encoding="utf-8") as f:
        item_template = f.read()
        
    archive_links = ""
    for file in files:
        filename_core = file.replace(".html", "")
        if " " in filename_core:
            date_part, time_part = filename_core.split(" ")
            display_text = f"{time_part} 일일 퀀트 리포트"
            badge_html = get_badge_html(time_part)
        else:
            display_text = f"{filename_core} 아카이브 리포트"
            badge_html = '<span class="text-[10px] font-bold px-2 py-1 rounded-lg bg-slate-100 text-slate-600">기타</span>'

        item_html = item_template
        
        item_html = item_html.replace("{file}", file)
        item_html = item_html.replace("{badge_html}", badge_html)
        item_html = item_html.replace("{date_str}", display_text)
        archive_links += item_html
        
    return archive_links
    
def generate_index_html(today_date, archive_links, daily_filename):
    """3. 메인 허브 및 일일 리포트 통합 빌드 메인 함수"""
    
    # 1. 외부 HTML 템플릿 파일 읽어오기
    index_template_path = "html/index_template.html"
    with open(index_template_path, "r", encoding="utf-8") as f:
        index_template = f.read()
        
    # 2. 동적 데이터(날짜 및 AI 본문 내용) 치환
    index_template = index_template.replace("{today_date}", today_date)
    index_template = index_template.replace("{archive_links}", archive_links)  # 이 부분 추가!
    index_template = index_template.replace("{daily_filename}", daily_filename)
    
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
    ai_text = get_ai_analysis_and_backtest_data(GEMINI_API_KEY, raw_text)
    
    # 2. [필수] AI 응답이 끝나면 파이썬이 이 함수를 호출해서 CSV에 저장!
    save_to_backtest_csv(ai_text, today_date)
    
    # 1단계: 개별 리포트 생성
    daily_filename = create_daily_report(today_date, current_time, ai_text)
    
    # 2단계: 아카이브 링크 목록 컴파일
    archive_links = build_archive_links()

    # 3단계: 메인 인덱스 페이지(아카이브 허브) 조립 및 저장
    html_template = generate_html(today_date, archive_links, daily_filename)
    
    #GMAIL_APP_PASSWORD = os.environ.get("GMAIL_APP_PASSWORD")    # gg내 메일 주소 설정 (보내는 사람과 받는 사람 동일)
    #MY_EMAIL = os.environ.get("MY_EMAIL")
    #send_gmail_report(current_time, html_template, GMAIL_APP_PASSWORD, MY_EMAIL)

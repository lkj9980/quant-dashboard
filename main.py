import os
import google.generativeai as genai
from datetime import datetime

# 1. API 키 설정 (GitHub Secrets에서 가져옴)
genai.configure(api_key=os.environ["GEMINI_API_KEY"])

def get_ai_analysis():
    # 여기에 실제 데이터 수집 로직(yfinance 등)을 넣거나 
    # 간단히 Gemini에게 시황 분석을 요청합니다.
    model = genai.GenerativeModel('gemini-1.5-flash')
    response = model.generate_content("최근 나스닥과 코스피 시장 상황을 짧고 강렬하게 요약해줘.")
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

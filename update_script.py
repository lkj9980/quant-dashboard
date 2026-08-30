import glob
import re

for filepath in glob.glob("history/*.html"):
  with open(filepath, "r", encoding="utf-8") as f:
    content = f.read()

  body_split_idx = content.find("<body")
  if body_split_idx == -1:
    continue

  head_part = content[:body_split_idx]
  body_part = content[body_split_idx:]

  # 1. 헤드 안에서 chart.js 관련 스크립트와 관련 주석들을 전부 찾아내서 일단 싹 다 지워버림
  head_part = re.sub(
      r'(\s*<!--\s*Chart\.js CDN\s*-->)?\s*<script[^>]*chart[2]?\.js[^>]*></script>',
      '',
      head_part,
      flags=re.IGNORECASE,
  )
  # 혹시 모를 남은 주석 잔해도 제거
  head_part = re.sub(
      r'^\s*<!--\s*Chart\.js CDN\s*-->\s*', '', head_part, flags=re.MULTILINE
  )

  # 2. </head> 바로 직전에 깔끔한 단 하나의 공식 CDN 주석과 태그를 강제로 예쁘게 꽂아넣기
  # </head>를 찾아서 그 앞에 넣어준다
  if "</head>" in head_part:
    clean_script = (
        '    <!-- Chart.js CDN -->\n'
        '    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>\n'
    )
    head_part = head_part.replace("</head>", clean_script + "</head>")

  updated_content = head_part + body_part

  if content != updated_content:
    with open(filepath, "w", encoding="utf-8") as f:
      f.write(updated_content)
    filename = filepath.replace("\\", "/").split("/")[-1]
    print(f"헤드 완벽 정돈 완료: {filename}")

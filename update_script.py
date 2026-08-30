import glob
import re

for filepath in glob.glob("history/*.html"):
  with open(filepath, "r", encoding="utf-8") as f:
    content = f.read()

  # <body 태그 위치 찾기
  body_split_idx = content.find("<body")
  if body_split_idx == -1:
    continue

  # <head> 부분과 <body> 이후 부분 분리
  head_part = content[:body_split_idx]
  body_part = content[body_split_idx:]

  # <head> 내부에서만 chart 관련 스크립트 태그를 찾아서 고정된 경로로 변경
  new_head_part = re.sub(
      r'<script src="(?:https://cdn\.jsdelivr\.net/npm/chart\.js|\.\./[Cc]hart[2]?\.js|\.\./html/chart\.js)"></script>',
      '<!-- Chart.js CDN -->\n    <script src="../html/chart.js"></script>',
      head_part,
  )

  updated_content = new_head_part + body_part

  if content != updated_content:
    with open(filepath, "w", encoding="utf-8") as f:
      f.write(updated_content)
    filename = filepath.replace("\\", "/").split("/")[-1]
    print(f"헤드 복구 완료: {filename}")

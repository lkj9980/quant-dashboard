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

  # <head> 내부만 대상: 중복 주석이나 꼬인 스크립트를 깔끔하게 정리하고 공식 CDN 삽입
  new_head_part = re.sub(
      r'(?s)<!--\s*Chart\.js CDN\s*-->.*?(?:<script[^>]*chart\.js[^>]*></script>|\s*)*',
      '<!-- Chart.js CDN -->\n    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>\n',
      head_part,
  )

  updated_content = new_head_part + body_part

  if content != updated_content:
    with open(filepath, "w", encoding="utf-8") as f:
      f.write(updated_content)
    filename = filepath.replace("\\", "/").split("/")[-1]
    print(f"헤드만 정돈 완료: {filename}")

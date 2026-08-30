import glob

for filepath in glob.glob("history/*.html"):
  with open(filepath, "r", encoding="utf-8") as f:
    content = f.read()

  # <script src="../html/chart 패턴을 모두 quant-chart로 일괄 변경
  updated_content = content.replace(
      '<script src="../html/chart', '<script src="../html/quant-chart'
  )

  if content != updated_content:
    with open(filepath, "w", encoding="utf-8") as f:
      f.write(updated_content)
    filename = filepath.replace("\\", "/").split("/")[-1]
    print(f"파일명 일괄 변경 완료: {filename}")

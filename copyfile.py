import os
import shutil

base_dir = os.path.dirname(os.path.abspath(__file__))
src_path = os.path.join(base_dir, "history", "quant_log.csv")
dst_path = os.path.join(base_dir, "data", "quant_log.csv")

os.makedirs(os.path.dirname(dst_path), exist_ok=True)

if os.path.exists(src_path):
    shutil.move(src_path, dst_path)
    print(f"파일 이동 완료: {src_path} -> {dst_path}")
else:
    print(f"이동할 원본 파일이 없습니다: {src_path}")

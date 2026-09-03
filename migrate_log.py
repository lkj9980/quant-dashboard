import os
import shutil

base_dir = os.path.dirname(os.path.abspath(__file__))

# 예시: 최신 index.html을 history 폴더 쪽으로 백업/아카이브할 때
src_path = os.path.join(base_dir, "index.html")
dst_path = os.path.join(base_dir, "index_backup.html")  # 또는 타임스탬프 조합

os.makedirs(os.path.dirname(dst_path), exist_ok=True)

if os.path.exists(src_path):
    #shutil.move(src_path, dst_path)
    shutil.copy(src_path, dst_path)
    print(f"파일 이동 완료: {src_path} -> {dst_path}")
else:
    print(f"이동할 원본 파일이 없습니다: {src_path}")

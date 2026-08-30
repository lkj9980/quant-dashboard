import os

# history 폴더 경로 (필요에 따라 경로를 수정하세요)
history_dir = "./history"

# 변경할 대상 문자열 (기존에 쓰이던 로컬 경로 패턴 등)과 바꿀 CDN 태그
# 예시로 흔히 쓰이는 로컬 경로 패턴을 찾아서 바꿉니다.
# 올바른 CDN 태그
cdn_script = '<script src="https://cdn.jsdelivr.net/npm/chart.js"></script>'
org_str = '<script src="https://cdn.jsdelivr.5net/npm/chart.js"></script>'
replacement_str = '<script src="../html/chart.js"></script>'

if not os.path.exists(history_dir):
    print(f"오류: '{history_dir}' 폴더를 찾을 수 없습니다.")
else:
    count = 0
    # history 폴더 내부 파일 순회
    for filename in os.listdir(history_dir):
        if filename.endswith(".html"):
            file_path = os.path.join(history_dir, filename)
            
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
            
            # 대상을 찾아 CDN 태그로 교체 
            # (만약 기존 파일들의 스크립트 태그 형태가 다양하다면 정규식을 쓰거나 여러 개를 replace 하실 수 있습니다)
            if cdn_script in content:
                # 유연하게 기존 chart.js 관련 스크립트 태그를 통째로 교체하려면 아래처럼 패턴을 맞추거나
                # 정규식을 쓸 수 있지만, 일단 가장 안전한 문자열 치환 방식을 사용합니다.
                updated_content = content
                # 2026-08-29 00:38 기준 분기
                if file_dt < split_dt:
                    replacement_str = '<script src="../html/chart.js"></script>'
                else:
                    replacement_str = '<script src="../html/chart2.js"></script>'
                    
                # 여러 형태의 기존 스크립트 태그를 CDN 태그로 일괄 교체
                updated_content = updated_content.replace(cdn_script, replacement_str)
                
            # 내용이 바뀐 경우에만 파일 저장
            if updated_content != content:
                with open(file_path, "w", encoding="utf-8") as f:
                    f.write(updated_content)
                count += 1
                print(f"변환 완료: {filename}")

    print(f"\n총 {count}개의 HTML 파일이 CDN 방식으로 수정되었습니다.")

"""
CLI 파이프라인: 이미지 파일 경로를 받아 학습용 멜로디 생성까지 수행
"""
import os
import sys
from pathlib import Path

from dotenv import load_dotenv

# 프로젝트 루트를 Python 경로에 추가
project_root = Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from src.core.mureka_utils import save_mureka_audio
from src.core.workflow import run_full_pipeline


def main(image_path: str | os.PathLike[str]) -> None:
    """이미지 파일 경로를 받아 전체 파이프라인 실행"""
    load_dotenv()
    openai_key = os.getenv("OPENAI_API_KEY")
    if not openai_key:
        raise RuntimeError("OPENAI_API_KEY가 설정되지 않았습니다.")

    image_file = Path(image_path)
    if not image_file.exists():
        raise FileNotFoundError(f"이미지 파일을 찾을 수 없습니다: {image_path}")

    # 이미지 파일 읽기
    image_bytes = image_file.read_bytes()
    print(f"[입력] 이미지: {image_path}")

    # 전체 파이프라인 실행
    suno_key = os.getenv("SUNO_API_KEY")
    result = run_full_pipeline(
        image_bytes,
        openai_key,
        suno_key=suno_key,
        wait_for_audio=True,
    )

    print("\n[추출 텍스트]\n", result["study_text"])
    print("\n[멜로디 가이드]\n", result["mnemonic_plan"])

    if suno_key and "suno_result" in result:
        suno_result = result["suno_result"]
        print("\n[Suno 결과]\n", suno_result)

        # 오디오 파일 저장
        audio_paths = save_mureka_audio(suno_result)
        if audio_paths:
            print("\n[저장 완료]")
            for path in audio_paths:
                print(f"- {path}")
        else:
            print("\n[Suno] 오디오 URL을 응답에서 찾지 못했습니다.")
    elif not suno_key:
        print("\n[Suno] SUNO_API_KEY가 없어서 노래 생성을 건너뜁니다.")


if __name__ == "__main__":
    # 예시 경로 수정 필요
    main("/Users/baehanjun/Desktop/스크린샷 2025-11-11 오후 6.28.45.png")
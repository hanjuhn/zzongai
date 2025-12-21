# dashboard_logs/logger.py
import csv
import time
from datetime import datetime
from pathlib import Path
from typing import List, Optional

PROJECT_ROOT = Path(__file__).resolve().parent.parent
LOG_DIR = PROJECT_ROOT / "dashboard_logs"
LOG_FILE = LOG_DIR / "real_melody_logs.csv"

# 감정 태그 풀 (서비스에서 쓰는 리스트랑 맞춰두면 좋음)
EMOTION_TAG_POOL: List[str] = [
    "통통튀는", "신나는", "슬픈", "밝은", "따뜻한",
    "차분한", "활기찬", "부드러운", "강렬한", "평화로운",
    "에너지 넘치는", "로맨틱한", "웃긴", "장난스러운", "진지한",
    "드라마틱한", "몽환적인", "우아한", "자유로운", "편안한",
]

# 간단한 event_id 카운터 (프로세스 기준, 서버 재시작되면 초기화됨)
# 필요하면 DB나 Redis로 바꿔도 됨
class EventIdGenerator:
    def __init__(self) -> None:
        self._current = 0

    def next(self) -> int:
        self._current += 1
        return self._current

event_id_gen = EventIdGenerator()


def init_log_file() -> None:
    """
    CSV 파일이 없으면 헤더를 만들어준다.
    """
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    if not LOG_FILE.exists():
        with LOG_FILE.open("w", newline="", encoding="utf-8-sig") as f:
            writer = csv.writer(f)
            writer.writerow([
                "event_id",
                "user_id",
                "created_at",
                "date",
                "emotion_tag",
                "emotion_tags",
                "upload_type",
                "text_length",
                "generation_time_sec",
                "retry_count",
                "success",
            ])


def log_generation_event(
    *,
    user_id: str,
    emotion_tags: Optional[List[str]],
    upload_type: str,
    text_length: int,
    generation_time_sec: float,
    retry_count: int = 0,
    success: bool = True,
) -> None:
    """
    실제 모델 호출이 끝난 후 한 줄씩 로그를 남기는 함수.
    FastAPI 엔드포인트에서 호출하면 됨.
    """
    init_log_file()

    now = datetime.now()
    event_id = event_id_gen.next()

    # emotion_tags 리스트 → 콤마로 join
    if emotion_tags and len(emotion_tags) > 0:
        primary_emotion = emotion_tags[0]
        emotion_tags_str = ",".join(emotion_tags)
    else:
        # 혹시 비어 있으면 Unknown 처리
        primary_emotion = "Unknown"
        emotion_tags_str = ""

    with LOG_FILE.open("a", newline="", encoding="utf-8-sig") as f:
        writer = csv.writer(f)
        writer.writerow([
            event_id,
            user_id,
            now.strftime("%Y-%m-%d %H:%M:%S"),
            now.date().isoformat(),
            primary_emotion,
            emotion_tags_str,
            upload_type,
            text_length,
            round(generation_time_sec, 2),
            retry_count,
            1 if success else 0,
        ])


class Timer:
    """
    with Timer() as t: 로 감싸서 t.elapsed 에 걸린 시간(초) 측정용
    """
    def __enter__(self):
        self._start = time.perf_counter()
        self.elapsed = 0.0
        return self

    def __exit__(self, exc_type, exc, tb):
        self.elapsed = time.perf_counter() - self._start
        # 예외가 나더라도 여기서 그냥 시간을 기록만 하고 넘김
        return False

import time
from typing import Any, Dict, Tuple, Optional, List

import requests


class SunoClient:
    """
    Suno API 클라이언트 래퍼
    
    Reference: https://api.sunoapi.org/docs
    """

    def __init__(
        self,
        api_key: str,
        base_url: str = "https://api.sunoapi.org/api/v1",
        poll_interval: float = 2.5,
        timeout_seconds: float = 600.0,
        verbose: bool = True,
    ) -> None:
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.poll_interval = poll_interval
        self.timeout_seconds = timeout_seconds
        self.verbose = verbose

    def _headers(self) -> Dict[str, str]:
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "Accept": "application/json",
            "User-Agent": "melody-learning/1.0 (+requests)",
            "Connection": "close",
        }

    def create_song(self, payload: Dict[str, Any]) -> str:
        """
        음악 생성 요청을 제출합니다. task_id를 반환합니다.
        """
        if not self.api_key:
            raise RuntimeError("SUNO_API_KEY 없어서 음악 생성 불가")

        url_generate = f"{self.base_url}/generate"
        if self.verbose:
            print(f"[Suno] POST {url_generate}")

        r = requests.post(url_generate, headers=self._headers(), json=payload, timeout=(10, 45))
        try:
            r.raise_for_status()
        except Exception:
            raise RuntimeError(f"Suno generate 실패: HTTP {r.status_code}\n본문: {r.text[:1000]}")

        try:
            data = r.json()
        except ValueError:
            raise RuntimeError(f"Suno generate 응답이 JSON 아님\n본문: {r.text[:1000]}")

        if self.verbose:
            print("[Suno] generate 응답:", str(data)[:1000])

        # 공통 에러 코드 처리
        if isinstance(data, dict) and data.get("code") and data["code"] != 200:
            raise RuntimeError(
                f"Suno generate 에러 code={data.get('code')}, "
                f"msg={data.get('msg') or data.get('message') or data}"
            )

        # 다양한 스키마에서 식별자 추출
        task_id = (
            data.get("data", {}).get("taskId")
            or data.get("data", {}).get("task_id")
            or data.get("data", {}).get("workId")
            or data.get("taskId")
            or data.get("task_id")
            or data.get("workId")
        )
        if not task_id:
            raise RuntimeError(f"Suno generate 응답에서 작업 ID(taskId/workId)를 찾지 못함: {data}")

        return str(task_id)

    def poll_result(self, task_id: str) -> Dict[str, Any]:
        """
        작업이 완료될 때까지 폴링합니다.
        """
        url_record = f"{self.base_url}/generate/record-info"
        start = time.time()
        attempt = 0
        last_status = None

        def parse_items(st: dict) -> Tuple[Optional[str], Optional[List[dict]]]:
            """
            상태 문자열과 결과 아이템 리스트를 다양한 스키마에서 추출.
            """
            data_field = st.get("data") or {}

            # 상태 문자열 후보
            status = (
                data_field.get("status")
                or st.get("status")
                or data_field.get("taskStatus")
                or st.get("taskStatus")
            )

            # 결과 blob
            resp = data_field.get("response")  # dict 또는 None
            raw = None
            if isinstance(resp, dict):
                raw = resp.get("sunoData") or resp.get("data") or resp.get("songs")
            if raw is None:
                raw = data_field.get("sunoData") or data_field.get("data") or st.get("result")

            # raw 정규화: list로
            if isinstance(raw, dict):
                raw = [raw]
            if raw is not None and not isinstance(raw, list):
                raw = None

            # 아이템 정규화: 공통 키로 맞춤
            items = None
            if raw:
                items = []
                for it in raw:
                    if not isinstance(it, dict):
                        continue
                    items.append({
                        "id": it.get("id") or it.get("musicId") or it.get("songId"),
                        "title": it.get("title") or data_field.get("title") or "Learning Song",
                        "audioUrl": it.get("audioUrl") or it.get("sourceAudioUrl") or it.get("streamAudioUrl"),
                        "imageUrl": it.get("imageUrl") or it.get("coverUrl"),
                        "raw": it,
                    })
                if not items:
                    items = None

            return status, items

        while time.time() - start < self.timeout_seconds:
            attempt += 1
            if attempt > 1:
                # 점진적 백오프(최대 8초)
                time.sleep(min(self.poll_interval * (1 + attempt * 0.25), 8.0))

            # --- GET 시도 ---
            try:
                s = requests.get(
                    url_record,
                    headers=self._headers(),
                    params={"taskId": task_id, "task_id": task_id, "workId": task_id},
                    timeout=(10, 45),
                )
                if s.status_code == 200:
                    try:
                        st = s.json()
                    except ValueError:
                        st = None
                    if st:
                        if self.verbose and (attempt % 3 == 1):
                            print("[Suno][GET] 응답:", str(st)[:800])
                        if st.get("code") and st["code"] != 200:
                            raise RuntimeError(
                                f"Suno record-info 에러 GET code={st.get('code')}, "
                                f"msg={st.get('msg') or st.get('message') or st}"
                            )
                        status, items = parse_items(st)
                        if status and status != last_status:
                            last_status = status
                            if self.verbose:
                                print(f"[Suno] status={status} (attempt {attempt})")
                        if status in {"SUCCESS", "DONE", "COMPLETED"}:
                            if items:
                                return {"task_id": task_id, "tracks": items, "status": status}
                            continue
                        if status in {"FAILED", "ERROR"}:
                            raise RuntimeError(f"Suno 생성 실패 상태 수신(GET): {st}")
                        continue
            except requests.exceptions.RequestException:
                pass

            # --- POST 폴백 ---
            try:
                s = requests.post(
                    url_record,
                    headers=self._headers(),
                    json={"taskId": task_id, "task_id": task_id, "workId": task_id},
                    timeout=(10, 45),
                )
                if s.status_code == 200:
                    try:
                        st = s.json()
                    except ValueError:
                        st = None
                    if st:
                        if self.verbose and (attempt % 3 == 1):
                            print("[Suno][POST] 응답:", str(st)[:800])
                        if st.get("code") and st["code"] != 200:
                            raise RuntimeError(
                                f"Suno record-info 에러 POST code={st.get('code')}, "
                                f"msg={st.get('msg') or st.get('message') or st}"
                            )
                        status, items = parse_items(st)
                        if status and status != last_status:
                            last_status = status
                            if self.verbose:
                                print(f"[Suno] status={status} (attempt {attempt})")
                        if status in {"SUCCESS", "DONE", "COMPLETED"}:
                            if items:
                                return {"task_id": task_id, "tracks": items, "status": status}
                            continue
                        if status in {"FAILED", "ERROR"}:
                            raise RuntimeError(f"Suno 생성 실패 상태 수신(POST): {st}")
                        continue
            except requests.exceptions.RequestException:
                continue

        # 타임아웃 시 마지막 상태라도 알리기
        raise TimeoutError(
            f"Suno 생성 대기 시간 초과 (마지막 status={last_status}, task_id={task_id})"
        )

    def generate_and_wait(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        음악 생성 요청을 제출하고 완료될 때까지 대기합니다.
        """
        task_id = self.create_song(payload)
        return self.poll_result(task_id)


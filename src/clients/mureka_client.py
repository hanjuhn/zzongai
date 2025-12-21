import time
from typing import Any, Dict

import requests
from requests import HTTPError


class MurekaClient:
    """
    Minimal wrapper for the Mureka song generation API.

    Reference: https://platform.mureka.ai/docs/en/quickstart.html
    """

    def __init__(
        self,
        api_key: str,
        base_url: str = "https://api.mureka.ai/v1",
        poll_interval: float = 5.0,
        timeout_seconds: float = 180.0,
        max_retries: int = 3,
        retry_backoff: float = 10.0,
    ) -> None:
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.poll_interval = poll_interval
        self.timeout_seconds = timeout_seconds
        self.max_retries = max_retries
        self.retry_backoff = retry_backoff

    def _headers(self) -> Dict[str, str]:
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

    def create_song(self, payload: Dict[str, Any]) -> str:
        """
        Submit a generation request. Returns the task ID.
        Retries on 429 responses with exponential backoff.
        """
        url = f"{self.base_url}/song/generate"
        attempt = 0
        backoff = self.retry_backoff
        while True:
            try:
                resp = requests.post(url, json=payload, headers=self._headers(), timeout=30)
                resp.raise_for_status()
                data = resp.json()
                task_id = data.get("id")
                if not task_id:
                    raise RuntimeError(f"Mureka API 응답에서 id를 찾을 수 없습니다: {data}")
                return task_id
            except HTTPError as exc:
                status = exc.response.status_code if exc.response is not None else None
                if status == 429 and attempt < self.max_retries:
                    attempt += 1
                    wait_seconds = backoff * attempt
                    time.sleep(wait_seconds)
                    continue
                raise

    def poll_result(self, task_id: str) -> Dict[str, Any]:
        """
        Poll the task endpoint until completion or failure.
        """
        url = f"{self.base_url}/song/tasks/{task_id}"
        elapsed = 0.0
        while elapsed <= self.timeout_seconds:
            resp = requests.get(url, headers=self._headers(), timeout=30)
            resp.raise_for_status()
            data = resp.json()
            status = data.get("status")
            if status in {"completed", "succeeded", "failed"}:
                return data
            time.sleep(self.poll_interval)
            elapsed += self.poll_interval
        raise TimeoutError("Mureka API 응답 대기 시간 초과")

    def generate_and_wait(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        task_id = self.create_song(payload)
        return self.poll_result(task_id)


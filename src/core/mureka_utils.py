import os
import pathlib
import time
from typing import Iterable, List, Sequence

import requests


def find_audio_urls(payload: object) -> List[str]:
    """
    Recursively search the payload (dict/list) for audio URLs.
    Returns a flat list of unique URLs.
    """
    collected = []
    seen = set()
    for url in _iter_audio_urls(payload):
        if url not in seen:
            collected.append(url)
            seen.add(url)
    return collected


def save_audio_files(
    urls: Sequence[str],
    output_dir: str | os.PathLike[str] = "outputs/mureka",
    timeout: int = 120,
) -> List[str]:
    """
    Download audio files from the provided URLs and persist them to disk.
    Returns the list of file paths written.
    """
    output_path = pathlib.Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    saved_files: List[str] = []
    for idx, url in enumerate(urls, start=1):
        try:
            file_ext = _infer_extension(url)
            timestamp = int(time.time())
            file_name = f"audio_{timestamp}_{idx}.{file_ext}"
            dest = output_path / file_name

            resp = requests.get(url, timeout=timeout)
            resp.raise_for_status()
            dest.write_bytes(resp.content)
            saved_files.append(str(dest.resolve()))
        except Exception as exc:  # pragma: no cover - log only
            print(f"[오디오] 저장 실패 ({url}): {exc}")

    return saved_files


def save_mureka_audio(
    result: dict,
    output_dir: str | os.PathLike[str] = "outputs/mureka",
    timeout: int = 120,
) -> List[str]:
    """
    Convenience wrapper: extract audio URLs from a Mureka response and download them.
    """
    urls = find_audio_urls(result)
    return save_audio_files(urls, output_dir=output_dir, timeout=timeout)


def _iter_audio_urls(payload: object) -> Iterable[str]:
    if isinstance(payload, dict):
        for key, value in payload.items():
            # Suno 형식: "audioUrl" 키 지원 추가
            if key in {"audio_url", "song_url", "url", "audioUrl", "sourceAudioUrl", "streamAudioUrl"} and _looks_like_audio(value):
                yield value  # type: ignore[misc]
            elif key in {"audio_urls", "song_urls", "tracks"} and isinstance(value, list):
                # "tracks"는 Suno 응답 형식 (리스트 안에 dict들이 있음)
                for item in value:
                    if isinstance(item, dict):
                        # dict 안에서 audioUrl 찾기
                        for audio_key in {"audioUrl", "sourceAudioUrl", "streamAudioUrl", "audio_url", "song_url", "url"}:
                            if audio_key in item and _looks_like_audio(item[audio_key]):
                                yield item[audio_key]  # type: ignore[misc]
                    elif _looks_like_audio(item):
                        yield item  # type: ignore[misc]
            else:
                yield from _iter_audio_urls(value)
    elif isinstance(payload, list):
        for item in payload:
            yield from _iter_audio_urls(item)


def _looks_like_audio(value: object) -> bool:
    if not isinstance(value, str):
        return False
    lowered = value.lower()
    return lowered.startswith("http") and any(ext in lowered for ext in (".mp3", ".wav", ".m4a", ".aac"))


def _infer_extension(url: str) -> str:
    lowered = url.lower()
    for ext in ("mp3", "wav", "m4a", "aac"):
        if lowered.endswith(f".{ext}"):
            return ext
    return "mp3"


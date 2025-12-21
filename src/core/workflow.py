from __future__ import annotations

import base64
import sys
from pathlib import Path
from typing import Any, Dict, Optional

from openai import OpenAI

# 프로젝트 루트를 Python 경로에 추가
project_root = Path(__file__).parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from src.rag.agents.generator_agent import GeneratorAgent
from src.lyrics.compose_prompt import build_suno_payload
from src.clients.suno_client import SunoClient
from src.processors.vision_to_query import image_bytes_to_study_text
from src.lyrics.lyrics_extractor import extract_final_lyrics


def extract_study_text(
    image_bytes: bytes,
    api_key: str,
    model: str = "gpt-4o-mini",
) -> str:
    return image_bytes_to_study_text(image_bytes, api_key, model=model)


def extract_study_text_from_base64(
    image_b64: str,
    api_key: str,
    model: str = "gpt-4o-mini",
) -> str:
    header, _, data = image_b64.partition(",")
    if data:
        encoded = data
    else:
        encoded = header
    image_bytes = base64.b64decode(encoded)
    return extract_study_text(image_bytes, api_key, model=model)


def create_mnemonic_plan(
    study_text: str,
    api_key: str,
    final_lyrics: str = None,
    model: str = "gpt-4o-mini",
) -> str:
    generator_agent = GeneratorAgent(api_key=api_key, model=model)
    return generator_agent.generate_mnemonic_plan(study_text, final_lyrics=final_lyrics)


def build_suno_request(study_text: str, mnemonic_plan: str, final_lyrics: str = None, api_key: Optional[str] = None, emotion_tags: Optional[list] = None, retrieved_docs: Optional[list] = None, reasoner_result: Optional[dict] = None) -> Dict[str, Any]:
    # 최종 가사가 제공되면 그걸 사용, 없으면 멜로디 가이드에서 추출
    if not final_lyrics:
        final_lyrics = extract_final_lyrics(mnemonic_plan)
        if not final_lyrics:
            final_lyrics = study_text  # 폴백
    
    return build_suno_payload(mnemonic_plan, study_text, final_lyrics=final_lyrics, api_key=api_key, emotion_tags=emotion_tags, retrieved_docs=retrieved_docs, reasoner_result=reasoner_result)


def request_suno_song(
    payload: Dict[str, Any],
    api_key: str,
    wait: bool = True,
    **client_kwargs: Any,
) -> Dict[str, Any]:
    client = SunoClient(api_key=api_key, **client_kwargs)
    if wait:
        return client.generate_and_wait(payload)
    task_id = client.create_song(payload)
    return {"id": task_id}


def run_full_pipeline(
    image_bytes: bytes,
    openai_key: str,
    suno_key: Optional[str] = None,
    *,
    openai_model: str = "gpt-4o-mini",
    wait_for_audio: bool = True,
    **suno_kwargs: Any,
) -> Dict[str, Any]:
    study_text = extract_study_text(image_bytes, openai_key, model=openai_model)
    mnemonic_plan = create_mnemonic_plan(study_text, openai_key, model=openai_model)
    payload = build_suno_request(study_text, mnemonic_plan)

    result: Dict[str, Any] = {
        "study_text": study_text,
        "mnemonic_plan": mnemonic_plan,
        "suno_payload": payload,
    }

    if suno_key:
        song_result = request_suno_song(payload, suno_key, wait=wait_for_audio, **suno_kwargs)
        result["suno_result"] = song_result

    return result


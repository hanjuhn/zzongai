# src/compose_prompt.py
import os
from openai import OpenAI
from src.lyrics.lyrics_extractor import get_lyrics_from_mnemonic_plan

# Suno API 가사 길이 제한 (커스텀 모드)
MAX_LYRICS_LENGTH = 5000


def truncate_lyrics(lyrics: str, max_length: int = MAX_LYRICS_LENGTH) -> str:
    """
    가사를 최대 길이로 제한합니다.
    너무 길면 마지막 문장을 잘라서 자연스럽게 끝냅니다.
    """
    if len(lyrics) <= max_length:
        return lyrics
    
    # 최대 길이까지 자르기
    truncated = lyrics[:max_length]
    
    # 마지막 문장이 잘리지 않도록 조정
    # 마지막 줄바꿈이나 문장 끝을 찾아서 자르기
    last_newline = truncated.rfind('\n')
    last_period = truncated.rfind('.')
    last_exclamation = truncated.rfind('!')
    last_question = truncated.rfind('?')
    
    # 가장 마지막 문장 종료 기호 찾기
    last_sentence_end = max(last_period, last_exclamation, last_question)
    
    if last_sentence_end > max_length * 0.8:  # 80% 이상이면 문장 끝에서 자르기
        return truncated[:last_sentence_end + 1]
    elif last_newline > max_length * 0.8:  # 줄바꿈에서 자르기
        return truncated[:last_newline]
    else:
        # 그냥 최대 길이에서 자르기
        return truncated + "..."


def summarize_for_lyrics(text: str, api_key: str, max_length: int = MAX_LYRICS_LENGTH) -> str:
    """
    텍스트가 너무 길면 노래 가사로 만들 수 있도록 요약합니다.
    """
    if len(text) <= max_length:
        return text
    
    client = OpenAI(api_key=api_key)
    
    prompt = f"""다음 학습 자료를 노래 가사로 만들 수 있도록 핵심 내용만 간결하게 요약해주세요.
요약된 내용은 {max_length}자 이하여야 하며, 노래로 부를 수 있는 자연스러운 문장으로 작성해주세요.
중요한 정보는 빠뜨리지 말고, 반복되는 내용은 제거해주세요.

[원본 내용]
{text}

[요약된 가사]"""

    try:
        resp = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": "너는 학습 자료를 노래 가사로 변환하는 전문가입니다. 핵심 내용만 간결하게 요약하여 노래로 부를 수 있는 형태로 정리해줍니다."
                },
                {"role": "user", "content": prompt},
            ],
            temperature=0.5,
            max_tokens=2000,  # 충분한 토큰 할당
        )
        summarized = resp.choices[0].message.content.strip()
        
        # 요약 후에도 길면 잘라내기
        return truncate_lyrics(summarized, max_length)
    except Exception as e:
        # 요약 실패 시 그냥 잘라내기
        return truncate_lyrics(text, max_length)


def build_suno_payload(mnemonic_plan, study_text, final_lyrics: str = None, api_key: str = None, emotion_tags: list = None, retrieved_docs: list = None, reasoner_result: dict = None):
    """
    Build a request payload for Suno's song generation endpoint.
    Reference: https://api.sunoapi.org/docs
    
    Args:
        mnemonic_plan: 멜로디 가이드
        study_text: 학습 텍스트
        final_lyrics: 최종 가사 (제공되면 이걸 사용)
        api_key: OpenAI API 키 (가사가 너무 길 때 요약에 사용)
        emotion_tags: 감정 태그 리스트 (선택사항)
    """
    # 최종 가사가 제공되면 그걸 사용, 없으면 멜로디 가이드에서 추출
    if final_lyrics:
        lyrics = final_lyrics
    else:
        # 멜로디 가이드에서 최종 가창 가이드 가사(5번 항목) 추출
        lyrics = get_lyrics_from_mnemonic_plan(mnemonic_plan, study_text)
    
    # 가사 길이 확인 및 제한
    if len(lyrics) > MAX_LYRICS_LENGTH:
        if api_key:
            # API 키가 있으면 요약 시도
            lyrics = summarize_for_lyrics(lyrics, api_key, MAX_LYRICS_LENGTH)
        else:
            # API 키가 없으면 그냥 잘라내기
            lyrics = truncate_lyrics(lyrics, MAX_LYRICS_LENGTH)
    
    # 감정 태그를 스타일에 반영 (간결하게)
    emotion_style_parts = []
    if emotion_tags and len(emotion_tags) > 0:
        # 감정 태그를 영어로 변환하여 스타일에 추가 (간결한 버전)
        emotion_translations = {
            "통통튀는": "bouncy",
            "신나는": "energetic",
            "슬픈": "sad",
            "밝은": "bright",
            "따뜻한": "warm",
            "차분한": "calm",
            "활기찬": "lively",
            "부드러운": "soft",
            "강렬한": "intense",
            "평화로운": "peaceful",
            "에너지 넘치는": "energetic",
            "로맨틱한": "romantic",
            "웃긴": "funny",
            "장난스러운": "playful",
            "진지한": "serious",
            "드라마틱한": "dramatic",
            "몽환적인": "dreamy",
            "격렬한": "fierce",
            "우아한": "elegant",
            "자유로운": "free",
            "긴장감 있는": "tense",
            "편안한": "relaxed",
            "신비로운": "mysterious",
            "웅장한": "grand",
            "섬세한": "delicate",
            "역동적인": "dynamic",
            "감성적인": "emotional",
            "경쾌한": "light",
            "잔잔한": "tranquil",
            "열정적인": "passionate"
        }
        
        # 최대 3개만 선택하여 길이 제한
        for tag in emotion_tags[:3]:
            if tag in emotion_translations:
                emotion_style_parts.append(emotion_translations[tag])
    
    # 검색된 동요의 스타일 정보 추출 (간결하게)
    reference_style_parts = []
    if retrieved_docs and len(retrieved_docs) > 0:
        # 검색된 동요들의 특징을 스타일에 반영 (제목은 최대 2개만, 간결하게)
        reference_titles = [doc.get('title', '')[:20] for doc in retrieved_docs[:2]]  # 상위 2개만, 각 20자 제한
        if reference_titles:
            reference_style_parts.append(f"Korean children's song style")
    
    if reasoner_result:
        melody_style = reasoner_result.get("melody_style", "")
        rhythm_pattern = reasoner_result.get("rhythm_pattern", "")
        if melody_style and len(melody_style) <= 50:  # 길이 제한
            reference_style_parts.append(melody_style[:50])
        if rhythm_pattern and len(rhythm_pattern) <= 30:  # 길이 제한
            reference_style_parts.append(rhythm_pattern[:30])
    
    # 스타일을 최대한 간결하게 만들어서 가사에 집중
    # 두 개의 트랙을 생성: 하나는 여자 보컬, 다른 하나는 남자 보컬
    # 스타일을 최소화하여 가사가 정확히 반영되도록 함
    base_style = "Korean children's song"
    
    # 감정 태그만 간결하게 추가 (최대 2개)
    if emotion_style_parts:
        emotion_str = ", ".join(emotion_style_parts[:2])
        style_base = f"{base_style}, {emotion_str}"
    else:
        style_base = base_style
    
    # 여자 보컬과 남자 보컬 스타일 (간결하게)
    style_female = f"{style_base}, female vocal"
    style_male = f"{style_base}, male vocal"
    
    # 두 가지 스타일을 모두 포함 (Suno API가 두 개의 트랙을 생성하도록)
    # 같은 가사를 사용하도록 명시
    style = f"{style_female} | {style_male}"
    
    # 최종 스타일 길이 확인 및 제한 (1000자 제한)
    if len(style) > 1000:
        # 스타일을 더 줄이기
        style = f"{base_style}, female vocal | {base_style}, male vocal"
    
    # callBackUrl 설정 (환경 변수에서 가져오거나 기본값 사용)
    callback_url = os.getenv("SUNO_CALLBACK_URL", "https://httpbin.org/post")
    
    # 가사 정리 (불필요한 공백, 줄바꿈 정리)
    # 가사는 그대로 유지 (줄바꿈은 유지하여 구조 보존)
    lyrics_cleaned = lyrics.strip()
    
    # 빈 줄은 하나로 정리하되, 가사 구조는 유지
    lines = [line.strip() for line in lyrics_cleaned.split("\n")]
    lyrics_cleaned = "\n".join([line for line in lines if line])  # 빈 줄만 제거
    
    # 가사가 비어있으면 에러
    if not lyrics_cleaned:
        raise ValueError("가사가 비어있습니다.")
    
    # 디버깅: 전달되는 가사 확인
    if os.getenv("DEBUG", "").lower() == "true":
        print(f"[DEBUG] Suno API에 전달될 가사 (원본 길이: {len(lyrics)}):")
        print(lyrics_cleaned[:300] + "..." if len(lyrics_cleaned) > 300 else lyrics_cleaned)
    
    # Suno API에 가사를 정확히 전달하기 위한 페이로드
    # customMode에서 prompt가 가사로 직접 사용됨 (순수 가사만 전달, 지시사항 없이)
    payload = {
        "customMode": True,
        "instrumental": False,
        "model": "V4_5",  # V3_5 | V4 | V4_5 | V4_5PLUS | V5
        "style": style,
        "title": "Learning Song",
        # 커스텀 모드에서 prompt가 가사로 직접 사용됨
        # 순수 가사만 전달 (지시사항이나 설명 없이)
        "prompt": lyrics_cleaned,
        "callBackUrl": callback_url,
        "callbackUrl": callback_url,  # 두 가지 형식 모두 지원
    }
    
    # 디버깅을 위한 로그 (항상 출력하여 가사 확인)
    print(f"[Suno] 전달되는 가사 (길이: {len(lyrics_cleaned)}자):")
    print(lyrics_cleaned[:200] + "..." if len(lyrics_cleaned) > 200 else lyrics_cleaned)
    print(f"[Suno] 스타일: {style[:100]}...")
    print(f"[Suno] 페이로드 prompt 필드 (처음 100자): {payload.get('prompt', '')[:100]}...")
    
    return payload
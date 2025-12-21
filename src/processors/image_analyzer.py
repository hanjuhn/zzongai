"""
이미지 타입별 분석 모듈
텍스트 이미지, 수식 이미지, 지도 이미지 등을 분석하여 학습용 내용을 생성
"""
import base64
from typing import Dict, List, Optional
from openai import OpenAI


def analyze_image_for_education(
    image_b64: str,
    client: OpenAI,
    model: str = "gpt-4o-mini"
) -> str:
    """
    이미지를 교육용 관점에서 분석하여 학습용 텍스트를 생성합니다.
    - 텍스트가 포함된 이미지: 텍스트 추출
    - 수식 이미지: 수식을 설명하고 음으로 표현할 수 있는 방식으로 변환
    - 지도 이미지: 관련 역사/지리 정보를 요약하여 가사로 만들 수 있는 내용 생성
    """
    
    prompt = """이 이미지를 교육용 학습 자료로 분석해주세요.

이미지 타입에 따라 다음과 같이 처리해주세요:

1. **텍스트가 포함된 이미지**: 이미지 안의 모든 텍스트를 정확히 추출하고, 줄바꿈을 유지해주세요.

2. **수식/수학 문제 이미지**: 수식을 읽을 수 있는 형태로 변환하고, 각 기호와 숫자를 음으로 표현할 수 있도록 설명해주세요. 
   예: "2 + 3 = 5" → "이 더하기 삼은 오" 또는 "2 플러스 3은 5"

3. **지도 이미지**: 지도에 표시된 지역의 주요 정보(역사, 지리, 문화 등)를 요약하여 노래 가사로 만들 수 있는 형태로 정리해주세요.
   예: "대한민국 지도" → "대한민국은 한반도에 위치한 나라입니다. 서울이 수도이고, 1948년에 건국되었습니다..."

4. **다이어그램/차트**: 주요 내용을 요약하여 학습하기 쉬운 형태로 정리해주세요.

출력 형식:
- 텍스트만 있는 경우: 텍스트 그대로 출력
- 수식/지도/다이어그램: 학습용 설명을 포함하여 출력
- 여러 요소가 섞인 경우: 모두 포함하여 출력

추출된 내용 외에는 아무 말도 하지 마세요."""

    try:
        resp = client.chat.completions.create(
            model=model,
            messages=[
                {
                    "role": "system",
                    "content": "너는 교육용 학습 자료 분석 전문가입니다. 이미지를 분석하여 학습자가 노래로 외울 수 있는 형태로 내용을 정리해줍니다."
                },
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{image_b64}"}},
                    ],
                },
            ],
            temperature=0.3,
        )
        return resp.choices[0].message.content.strip()
    except Exception as e:
        raise RuntimeError(f"이미지 분석 실패: {str(e)}")


def analyze_multiple_images(
    image_b64_list: List[str],
    api_key: str,
    model: str = "gpt-4o-mini"
) -> str:
    """
    여러 이미지를 분석하고 종합하여 학습용 텍스트를 생성합니다.
    """
    client = OpenAI(api_key=api_key)
    
    # 각 이미지 분석
    analyzed_texts = []
    for i, image_b64 in enumerate(image_b64_list, 1):
        try:
            text = analyze_image_for_education(image_b64, client, model)
            analyzed_texts.append(f"[이미지 {i}]\n{text}")
        except Exception as e:
            analyzed_texts.append(f"[이미지 {i}] 분석 실패: {str(e)}")
    
    # 여러 이미지 내용을 종합하여 요약
    if len(analyzed_texts) > 1:
        combined_text = "\n\n".join(analyzed_texts)
        
        summary_prompt = f"""다음은 여러 학습 자료에서 추출한 내용입니다. 
이 내용들을 종합하여 하나의 일관된 학습 자료로 정리해주세요.
중복되는 내용은 제거하고, 핵심 내용만 간결하게 정리해주세요.
노래 가사로 만들 수 있도록 자연스러운 문장으로 작성해주세요.

[추출된 내용]
{combined_text}

[요약된 학습 자료]"""

        try:
            resp = client.chat.completions.create(
                model=model,
                messages=[
                    {
                        "role": "system",
                        "content": "너는 교육 자료 요약 전문가입니다. 여러 자료를 종합하여 학습자가 쉽게 외울 수 있는 형태로 정리해줍니다."
                    },
                    {"role": "user", "content": summary_prompt},
                ],
                temperature=0.5,
            )
            return resp.choices[0].message.content.strip()
        except Exception:
            # 요약 실패 시 원본 텍스트 반환
            return combined_text
    
    return analyzed_texts[0] if analyzed_texts else ""


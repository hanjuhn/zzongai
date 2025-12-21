# src/vision_to_query.py
import base64
from openai import OpenAI


def encode_image(path):
    with open(path, "rb") as f:
        return base64.b64encode(f.read()).decode("utf-8")


def image_bytes_to_study_text(image_bytes, api_key, model="gpt-4o-mini"):
    """
    OCR-like helper that extracts readable text from raw image bytes.
    """
    client = OpenAI(api_key=api_key)
    b64 = base64.b64encode(image_bytes).decode("utf-8")
    return _image_b64_to_study_text(b64, client, model=model)


def image_to_study_text(image_path, api_key, model="gpt-4o-mini"):
    """
    Convenience wrapper that loads the image from disk before delegating to the
    byte-processing helper.
    """
    b64 = encode_image(image_path)
    client = OpenAI(api_key=api_key)
    return _image_b64_to_study_text(b64, client, model=model)


def _image_b64_to_study_text(image_b64, client: OpenAI, model="gpt-4o-mini"):
    prompt = (
        "이미지 안에서 읽을 수 있는 문자만 정확히 추출해줘. "
        "가능하면 줄바꿈을 유지하고, 장식 표현은 빼고 글자 그대로 돌려줘. "
        "추출된 텍스트 외에는 아무 말도 하지 마."
    )
    resp = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": "너는 고정밀 OCR 보조자. 한국어와 숫자 기호를 그대로 전달해."},
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{image_b64}"}},
                ],
            },
        ],
        temperature=0.0,
    )
    return resp.choices[0].message.content.strip()
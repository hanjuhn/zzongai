"""
Query Understanding Agent
사용자의 질문을 분석하고 검색 쿼리 형태로 변환
"""
from typing import Dict, Any
from openai import OpenAI


class QueryUnderstandingAgent:
    """질문 해석 에이전트"""
    
    def __init__(self, api_key: str, model: str = "gpt-4o-mini"):
        """
        Args:
            api_key: OpenAI API 키
            model: 사용할 모델
        """
        self.client = OpenAI(api_key=api_key)
        self.model = model
    
    def process(self, user_query: str) -> Dict[str, Any]:
        """
        사용자 질문을 분석하고 검색 쿼리로 변환
        
        Args:
            user_query: 사용자 질문 또는 학습 텍스트
            
        Returns:
            {
                "search_query": 검색 쿼리,
                "categories": 추출된 카테고리 (주제, 감정, 계절, 동물, 행동 등),
                "intent": 사용자 의도
            }
        """
        prompt = f"""다음 사용자 질문 또는 학습 텍스트를 분석하여 검색 쿼리와 카테고리를 추출해주세요.

[사용자 입력]
{user_query}

[출력 포맷]
다음 JSON 형식으로만 출력해주세요:
{{
    "search_query": "검색에 사용할 핵심 키워드나 문장",
    "categories": {{
        "주제": "주제 키워드 (없으면 빈 문자열)",
        "감정": "감정 키워드 (없으면 빈 문자열)",
        "계절": "계절 키워드 (없으면 빈 문자열)",
        "동물": "동물 키워드 (없으면 빈 문자열)",
        "행동": "행동 키워드 (없으면 빈 문자열)"
    }},
    "intent": "사용자의 의도 (가사 생성, 동요 추천, 스타일 분석 등)"
}}

[요구사항]
- search_query는 벡터 검색에 최적화된 형태로 작성
- 카테고리는 해당하는 것만 추출하고, 없으면 빈 문자열로 표시
- intent는 간결하게 한 문장으로 작성
- JSON 형식만 출력하고 다른 설명은 하지 마세요"""

        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {
                    "role": "system",
                    "content": "너는 사용자 질문을 분석하여 검색 쿼리와 카테고리를 추출하는 전문가입니다. JSON 형식으로만 답변합니다."
                },
                {"role": "user", "content": prompt}
            ],
            temperature=0.3,
            response_format={"type": "json_object"}
        )
        
        import json
        result = json.loads(response.choices[0].message.content.strip())
        
        return {
            "search_query": result.get("search_query", user_query),
            "categories": result.get("categories", {}),
            "intent": result.get("intent", "가사 생성"),
            "original_query": user_query
        }
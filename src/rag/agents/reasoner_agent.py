"""
Reasoner Agent
Query Agent 결과와 Retriever Agent 결과를 통합하여 최종 답변 생성
"""
from typing import Dict, Any, List
from openai import OpenAI


class ReasonerAgent:
    """응답 조합 에이전트"""
    
    def __init__(self, api_key: str, model: str = "gpt-4o-mini"):
        """
        Args:
            api_key: OpenAI API 키
            model: 사용할 모델
        """
        self.client = OpenAI(api_key=api_key)
        self.model = model
    
    def reason(
        self,
        query_result: Dict[str, Any],
        retrieved_docs: List[Dict[str, Any]],
        task_type: str = "lyrics_generation"
    ) -> Dict[str, Any]:
        """
        Query 결과와 검색된 문서를 통합하여 최종 답변 생성
        
        Args:
            query_result: Query Agent 결과
            retrieved_docs: Retriever Agent 결과
            task_type: 작업 유형 (lyrics_generation, style_analysis, recommendation 등)
            
        Returns:
            {
                "reasoning": 추론 과정,
                "recommendations": 추천 사항,
                "style_guide": 스타일 가이드,
                "context_summary": 컨텍스트 요약
            }
        """
        # 검색된 문서를 컨텍스트로 포맷팅 (가사 포함)
        context = ""
        if retrieved_docs:
            context = "\n[참고 동요 정보]\n"
            for i, doc in enumerate(retrieved_docs, 1):
                context += f"\n{i}. {doc['title']}\n"
                context += f"   특징: {doc['feature_summary']}\n"
                if doc.get('lyrics'):
                    # 가사 전체 또는 일부를 포함하여 운율/리듬 분석 가능하도록
                    lyrics_preview = doc['lyrics'][:300] if len(doc['lyrics']) > 300 else doc['lyrics']
                    context += f"   가사: {lyrics_preview}\n"
        
        categories_str = ", ".join([
            f"{k}: {v}" for k, v in query_result.get("categories", {}).items() 
            if v
        ])
        
        prompt = f"""[Chain-of-Thought 추론 과정]

다음 단계를 따라 추론과 가이드를 생성하세요:

**1단계: 사용자 의도 분석**
- 사용자가 무엇을 원하는지 정확히 파악하세요.
- 사용자 의도: {query_result.get('intent', '가사 생성')}
- 추출된 카테고리: {categories_str if categories_str else "없음"}

**2단계: 검색된 동요 분석**
{context if context else "- 검색된 동요 없음"}
- 각 동요의 특징, 가사 구조, 리듬, 운율을 분석하세요.
- 공통점과 차이점을 파악하세요.

**3단계: 사용자 요청과 동요 매칭**
- 사용자의 학습 텍스트와 검색된 동요들을 연결하세요.
- 어떤 동요의 스타일이 가장 적합한지 판단하세요.
- 원본 질문: {query_result.get('original_query', '')}

**4단계: 가락/운율/리듬 패턴 추출**
- 검색된 동요들의 가락 스타일을 분석하세요.
- 리듬 패턴을 식별하세요 (4/4박자, 3/4박자, 경쾌한 8비트 등).
- 운율 패턴을 분석하세요 (AABB, ABAB, ABCB 등).

**5단계: 최종 가이드 생성**
- 위 분석을 종합하여 가사 생성 가이드를 만드세요.

[출력 포맷]
다음 JSON 형식으로만 출력해주세요:
{{
    "reasoning": "검색된 동요들과 사용자 요청을 통합한 논리적 추론 과정 (1-3단계 종합)",
    "recommendations": "가사 생성 시 고려할 구체적이고 실행 가능한 사항들 (운율, 리듬, 가락 패턴 포함)",
    "style_guide": "추천하는 스타일과 톤 (예: 밝고 경쾌한, 따뜻한, 교육적인 등)",
    "context_summary": "참고할 동요들의 공통 특징 요약",
    "rhythm_pattern": "참고 동요들의 리듬 패턴 분석 결과 (예: 4/4박자, 경쾌한 8비트, 반복적인 리듬 등)",
    "melody_style": "참고 동요들의 가락 스타일 분석 결과 (예: 상행 멜로디, 반복적인 후렴구, 단순한 멜로디 라인 등)",
    "rhyme_scheme": "참고 동요들의 운율 패턴 분석 결과 (예: AABB, ABAB, ABCB 등)"
}}

[엄격한 요구사항]
- reasoning은 1-3단계의 논리적 추론 과정을 명확히 설명해야 합니다.
- recommendations는 구체적이고 실행 가능한 제안이어야 하며, 운율, 리듬, 가락 패턴을 구체적으로 포함해야 합니다.
- style_guide는 가사 생성 시 참고할 스타일을 명확히 제시해야 합니다.
- rhythm_pattern은 4단계에서 분석한 리듬 특징을 구체적으로 설명해야 합니다 (예: "4/4박자, 경쾌한 8비트, 후렴구에서 반복적인 리듬").
- melody_style은 4단계에서 분석한 가락 특징을 구체적으로 설명해야 합니다 (예: "상행 멜로디, 반복적인 후렴구, 단순한 멜로디 라인").
- rhyme_scheme은 4단계에서 분석한 운율 패턴을 구체적으로 제시해야 합니다 (예: "AABB 형식, 마지막 음절이 같은 운율").
- JSON 형식만 출력하고 다른 설명은 하지 마세요."""

        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "너는 다음 전문가들의 협업으로 검색된 정보와 사용자 요청을 통합하여 최적의 가이드를 제공하는 팀입니다:\n"
                        "1. **음악 분석가**: 동요의 가락, 운율, 리듬 패턴을 정확히 분석합니다.\n"
                        "2. **교육 전문가**: 학습 효과를 최적화하는 스타일을 추천합니다.\n"
                        "3. **작사 가이드 전문가**: 가사 생성에 필요한 구체적이고 실행 가능한 가이드를 제공합니다.\n"
                        "4. **패턴 분석가**: 검색된 동요들의 공통 패턴을 식별하고 추출합니다.\n\n"
                        "**절대 규칙**: JSON 형식으로만 답변하며, 모든 필드를 구체적이고 실행 가능한 내용으로 채워야 합니다."
                    )
                },
                {"role": "user", "content": prompt}
            ],
            temperature=0.3,  # 더 낮은 temperature로 일관성 향상
            response_format={"type": "json_object"}
        )
        
        import json
        result = json.loads(response.choices[0].message.content.strip())
        
        return {
            "reasoning": result.get("reasoning", ""),
            "recommendations": result.get("recommendations", ""),
            "style_guide": result.get("style_guide", ""),
            "context_summary": result.get("context_summary", ""),
            "rhythm_pattern": result.get("rhythm_pattern", ""),
            "melody_style": result.get("melody_style", ""),
            "rhyme_scheme": result.get("rhyme_scheme", ""),
            "categories": query_result.get("categories", {}),
            "intent": query_result.get("intent", "")
        }
"""
Self-RAG Agent
생성된 가사를 검증하고 개선하는 Self-RAG 과정
"""
from typing import Dict, Any, List, Optional
from openai import OpenAI


class SelfRAGAgent:
    """Self-RAG 에이전트: 생성된 가사를 검증하고 개선"""
    
    def __init__(self, api_key: str, model: str = "gpt-4o-mini"):
        """
        Args:
            api_key: OpenAI API 키
            model: 사용할 모델
        """
        self.client = OpenAI(api_key=api_key)
        self.model = model
    
    def verify_and_improve(
        self,
        generated_lyrics: str,
        study_text: str,
        retrieved_docs: List[Dict[str, Any]],
        reasoner_result: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        생성된 가사를 검증하고 개선
        
        Args:
            generated_lyrics: 생성된 가사
            study_text: 원본 학습 텍스트
            retrieved_docs: 검색된 동요 문서들
            reasoner_result: Reasoner Agent 결과
            
        Returns:
            {
                "improved_lyrics": 개선된 가사,
                "verification_result": 검증 결과,
                "improvements": 개선 사항 리스트
            }
        """
        # 검색된 동요 정보를 컨텍스트로 포맷팅
        context = ""
        if retrieved_docs:
            context = "\n[참고 동요 정보]\n"
            for i, doc in enumerate(retrieved_docs[:3], 1):  # 상위 3개만
                context += f"\n{i}. {doc.get('title', '')}\n"
                if doc.get('lyrics'):
                    lyrics_preview = doc['lyrics'][:200]  # 가사 일부만
                    context += f"   가사 일부: {lyrics_preview}...\n"
                if doc.get('feature_summary'):
                    context += f"   특징: {doc['feature_summary']}\n"
        
        # Self-RAG 검증 및 개선 프롬프트
        prompt = f"""생성된 가사를 검증하고 개선하세요.

[원본 학습 텍스트]
{study_text}

[생성된 가사]
{generated_lyrics}

{context}

[검증 및 개선 지침]
1. **내용 정확성 검증**: 생성된 가사가 원본 학습 텍스트의 핵심 내용을 정확히 반영하는지 확인하세요.
2. **누락된 정보 확인**: 원본 텍스트의 중요한 정보가 가사에서 누락되었는지 확인하세요.
3. **추가된 내용 확인**: 원본 텍스트에 없는 불필요한 내용이 추가되었는지 확인하세요.
4. **동요 스타일 검증**: 생성된 가사가 참고 동요들의 스타일과 일치하는지 확인하세요.
5. **리듬과 운율 검증**: 가사가 노래로 부르기 쉬운 리듬과 운율을 가지고 있는지 확인하세요.

[출력 형식]
다음 형식으로 응답하세요:

[검증 결과]
- 내용 정확성: (정확함/부분적/부정확)
- 정보 누락: (없음/있음 - 누락된 내용)
- 불필요한 추가: (없음/있음 - 추가된 내용)
- 스타일 일치: (일치함/부분적/불일치)
- 리듬/운율: (적절함/개선 필요)

[개선 사항]
(개선이 필요한 부분을 구체적으로 나열)

[개선된 가사]
(검증 결과를 바탕으로 개선된 가사를 작성하세요. 개선이 필요 없으면 원본 가사를 그대로 반환하세요)
**중요: 가사만 작성하고, 설명이나 평가 문구는 절대 포함하지 마세요.**
"""
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "너는 가사 검증 및 개선 전문가입니다. 생성된 가사를 검증하고 필요시 개선하여 더 정확하고 품질 높은 가사를 만들어줍니다."
                    },
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,  # 낮은 temperature로 일관성 유지
                max_tokens=1500,
            )
            
            result_text = response.choices[0].message.content.strip()
            
            # 결과 파싱
            improved_lyrics = self._extract_improved_lyrics(result_text, generated_lyrics)
            verification_result = self._extract_verification(result_text)
            improvements = self._extract_improvements(result_text)
            
            return {
                "improved_lyrics": improved_lyrics,
                "verification_result": verification_result,
                "improvements": improvements,
                "raw_result": result_text
            }
        except Exception as e:
            # 검증 실패 시 원본 가사 반환
            return {
                "improved_lyrics": generated_lyrics,
                "verification_result": {"error": str(e)},
                "improvements": [],
                "raw_result": ""
            }
    
    def _extract_improved_lyrics(self, result_text: str, original_lyrics: str) -> str:
        """개선된 가사 추출"""
        # "[개선된 가사]" 섹션 찾기
        import re
        pattern = r'\[개선된 가사\]\s*\n(.*?)(?=\n\[|\Z)'
        match = re.search(pattern, result_text, re.DOTALL)
        if match:
            improved = match.group(1).strip()
            if improved and len(improved) > 10:  # 의미있는 내용이 있으면
                # 설명 문구 제거
                improved = self._remove_explanation_text(improved)
                return improved
        
        # 추출 실패 시 원본 반환
        return original_lyrics
    
    def _remove_explanation_text(self, text: str) -> str:
        """가사에서 설명 문구 제거"""
        import re
        
        # 설명 문구 패턴들
        explanation_patterns = [
            r'이렇게\s+개선된\s+가사는.*',
            r'원본\s+내용의\s+핵심을.*',
            r'리듬과\s+운율도.*',
            r'개선된\s+가사는.*',
            r'이\s+가사는.*',
            r'위\s+가사는.*',
            r'다음\s+가사는.*',
            r'위의\s+가사는.*',
            r'개선\s+결과.*',
            r'검증\s+결과.*',
        ]
        
        lines = text.split('\n')
        cleaned_lines = []
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # 설명 문구 패턴과 일치하는지 확인
            is_explanation = False
            for pattern in explanation_patterns:
                if re.search(pattern, line, re.IGNORECASE):
                    is_explanation = True
                    break
            
            # 설명 문구가 아니고, 가사처럼 보이는 줄만 추가
            if not is_explanation:
                # 너무 긴 줄(설명일 가능성)은 제외
                if len(line) < 100:  # 가사 한 줄은 보통 100자 이하
                    cleaned_lines.append(line)
        
        # 빈 줄 제거 후 반환
        result = '\n'.join(cleaned_lines).strip()
        
        # 결과가 너무 짧으면 원본 반환
        if len(result) < 10:
            return text.strip()
        
        return result
    
    def _extract_verification(self, result_text: str) -> Dict[str, Any]:
        """검증 결과 추출"""
        import re
        verification = {}
        
        # "[검증 결과]" 섹션 찾기
        pattern = r'\[검증 결과\]\s*\n(.*?)(?=\n\[|\Z)'
        match = re.search(pattern, result_text, re.DOTALL)
        if match:
            verification_text = match.group(1)
            # 각 항목 추출
            for line in verification_text.split('\n'):
                if ':' in line:
                    key, value = line.split(':', 1)
                    key = key.strip().replace('-', '').strip()
                    value = value.strip()
                    if key and value:
                        verification[key] = value
        
        return verification
    
    def _extract_improvements(self, result_text: str) -> List[str]:
        """개선 사항 추출"""
        import re
        improvements = []
        
        # "[개선 사항]" 섹션 찾기
        pattern = r'\[개선 사항\]\s*\n(.*?)(?=\n\[|\Z)'
        match = re.search(pattern, result_text, re.DOTALL)
        if match:
            improvements_text = match.group(1)
            # 각 개선 사항 추출
            for line in improvements_text.split('\n'):
                line = line.strip()
                if line and (line.startswith('-') or line.startswith('•') or line.startswith('*')):
                    improvements.append(line.lstrip('-•*').strip())
                elif line and len(line) > 5:
                    improvements.append(line)
        
        return improvements
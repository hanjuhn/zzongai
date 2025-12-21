"""
멜로디 가이드에서 최종 가창 가이드 가사를 추출하는 모듈
"""
import re
from typing import Optional


def extract_final_lyrics(mnemonic_plan: str) -> Optional[str]:
    """
    멜로디 가이드에서 5번 항목인 "최종 가창 가이드 가사"를 추출합니다.
    
    Args:
        mnemonic_plan: 멜로디 가이드 전체 텍스트
        
    Returns:
        추출된 가사 또는 None
    """
    if not mnemonic_plan:
        return None
    
    # 여러 패턴으로 시도
    patterns = [
        # 패턴 1: "5) 최종 가창 가이드 가사" 또는 "5. 최종 가창 가이드 가사"
        r'5[\)\.]\s*최종\s*가창\s*가이드\s*가사[:\-]?\s*\n(.*?)(?=\n\s*6[\)\.]|\n\s*보너스|\Z)',
        # 패턴 2: "5) 최종 가창 가이드" (가사 생략)
        r'5[\)\.]\s*최종\s*가창\s*가이드[:\-]?\s*\n(.*?)(?=\n\s*6[\)\.]|\n\s*보너스|\Z)',
        # 패턴 3: "5)" 또는 "5." 다음에 가사가 오는 경우
        r'5[\)\.]\s*[^\n]*가사[:\-]?\s*\n(.*?)(?=\n\s*6[\)\.]|\n\s*보너스|\Z)',
        # 패턴 4: "최종 가창 가이드 가사" 키워드만 찾기
        r'최종\s*가창\s*가이드\s*가사[:\-]?\s*\n(.*?)(?=\n\s*(?:6[\)\.]|보너스)|\Z)',
    ]
    
    for pattern in patterns:
        match = re.search(pattern, mnemonic_plan, re.DOTALL | re.IGNORECASE)
        if match:
            lyrics = match.group(1).strip()
            if lyrics:
                # 불필요한 공백 정리
                lyrics = re.sub(r'\n{3,}', '\n\n', lyrics)
                return lyrics.strip()
    
    # 패턴 매칭 실패 시, "5)" 또는 "5." 다음 부분을 찾아보기
    lines = mnemonic_plan.split('\n')
    in_section_5 = False
    section_5_lines = []
    
    for line in lines:
        # 5번 섹션 시작 확인
        if re.match(r'^\s*5[\)\.]', line):
            in_section_5 = True
            # 헤더 라인은 제외하고 다음 줄부터
            continue
        # 6번 섹션 또는 보너스 섹션 시작 시 중단
        if in_section_5 and re.match(r'^\s*(6[\)\.]|보너스)', line):
            break
        # 5번 섹션 내의 내용 수집
        if in_section_5:
            line = line.strip()
            if line and not line.startswith('최종') and not line.startswith('가창') and not line.startswith('가이드'):
                section_5_lines.append(line)
    
    if section_5_lines:
        lyrics = '\n'.join(section_5_lines).strip()
        if lyrics:
            return lyrics
    
    return None


def get_lyrics_from_mnemonic_plan(mnemonic_plan: str, study_text: str = "") -> str:
    """
    멜로디 가이드에서 최종 가창 가이드 가사를 추출합니다.
    추출 실패 시 study_text를 사용합니다.
    
    Args:
        mnemonic_plan: 멜로디 가이드
        study_text: 학습 텍스트 (폴백용)
        
    Returns:
        가사 텍스트
    """
    final_lyrics = extract_final_lyrics(mnemonic_plan)
    
    if final_lyrics:
        return final_lyrics
    
    # 추출 실패 시 원본 텍스트 반환
    return study_text


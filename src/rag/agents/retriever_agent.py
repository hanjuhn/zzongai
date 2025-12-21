"""
Retriever Agent
벡터 DB에서 관련된 가사 또는 특징 요약을 검색
"""
from typing import List, Dict, Any, Optional
import numpy as np
import re
from openai import OpenAI
from src.rag.vector_db import DongyoVectorDB


class RetrieverAgent:
    """검색 에이전트"""
    
    def __init__(
        self, 
        api_key: str,
        embeddings_path: str = None,
        index_path: str = None,
        embedding_model: str = "text-embedding-3-small"
    ):
        """
        Args:
            api_key: OpenAI API 키
            embeddings_path: embeddings 파일 경로
            index_path: FAISS index 파일 경로
            embedding_model: 임베딩 모델
        """
        self.client = OpenAI(api_key=api_key)
        self.embedding_model = embedding_model
        self.db = DongyoVectorDB(embeddings_path=embeddings_path, index_path=index_path)
    
    def retrieve(
        self, 
        search_query: str, 
        top_k: int = 5,
        categories: Optional[Dict[str, str]] = None,
        use_hybrid: bool = True
    ) -> List[Dict[str, Any]]:
        """
        벡터 DB에서 관련 문서 검색 (하이브리드 검색 + 메타데이터 필터링)
        
        Args:
            search_query: 검색 쿼리
            top_k: 반환할 상위 k개 결과
            categories: 필터링할 카테고리 (주제, 감정, 계절, 동물, 행동 등)
            use_hybrid: 하이브리드 검색 사용 여부 (벡터 + 키워드)
            
        Returns:
            검색된 동요 정보 리스트
        """
        # 1. 벡터 검색 (의미적 유사성)
        response = self.client.embeddings.create(
            model=self.embedding_model,
            input=search_query
        )
        query_embedding = np.array(response.data[0].embedding, dtype=np.float32)
        
        # 벡터 검색 (더 많이 검색하여 후처리)
        vector_results = self.db.search_similar(query_embedding, top_k=top_k * 3 if use_hybrid else top_k)
        
        # 2. 하이브리드 검색: 키워드 검색 추가 (비용 없음)
        if use_hybrid:
            # 검색 쿼리에서 키워드 추출
            keywords = self._extract_keywords(search_query)
            if keywords:
                keyword_results = self.db.search_by_keywords(keywords, top_k=top_k * 2)
                
                # 벡터 검색과 키워드 검색 결과 결합
                # 벡터 검색 결과에 가중치 부여 (70%)
                # 키워드 검색 결과에 가중치 부여 (30%)
                combined_results = self._combine_results(vector_results, keyword_results, top_k=top_k * 2)
            else:
                combined_results = vector_results
        else:
            combined_results = vector_results
        
        # 3. 메타데이터 필터링 (카테고리 기반, 비용 없음)
        if categories:
            filtered_results = self.db.filter_by_categories(combined_results, categories)
        else:
            filtered_results = combined_results
        
        # 4. 최종 상위 k개 선택 (거리 기반)
        final_results = sorted(filtered_results, key=lambda x: x.get('distance', float('inf')))[:top_k]
        
        return final_results
    
    def _extract_keywords(self, text: str) -> List[str]:
        """
        텍스트에서 키워드 추출 (간단한 방법, 비용 없음)
        
        Args:
            text: 검색 쿼리 텍스트
            
        Returns:
            키워드 리스트
        """
        # 한국어와 영어 단어 추출
        words = re.findall(r'\b\w+\b', text.lower())
        # 2글자 이상의 단어만, 불용어 제거
        stopwords = {'the', 'is', 'are', 'was', 'were', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', '이', '가', '을', '를', '에', '의', '와', '과', '도', '로', '으로'}
        keywords = [w for w in words if len(w) >= 2 and w not in stopwords]
        return keywords[:10]  # 최대 10개
    
    def _combine_results(
        self,
        vector_results: List[Dict[str, Any]],
        keyword_results: List[Dict[str, Any]],
        top_k: int = 10
    ) -> List[Dict[str, Any]]:
        """
        벡터 검색과 키워드 검색 결과 결합 (비용 없음)
        
        Args:
            vector_results: 벡터 검색 결과
            keyword_results: 키워드 검색 결과
            top_k: 반환할 상위 k개
            
        Returns:
            결합된 결과 리스트
        """
        # 결과를 인덱스로 그룹화
        combined = {}
        
        # 벡터 검색 결과 (가중치 0.7)
        for result in vector_results:
            idx = result.get('index')
            if idx is not None:
                if idx not in combined:
                    combined[idx] = result.copy()
                    combined[idx]['combined_score'] = 0.0
                # 거리를 점수로 변환 (거리가 작을수록 점수 높음)
                distance = result.get('distance', float('inf'))
                score = 1.0 / (distance + 1) * 0.7
                combined[idx]['combined_score'] = combined[idx].get('combined_score', 0.0) + score
        
        # 키워드 검색 결과 (가중치 0.3)
        for result in keyword_results:
            idx = result.get('index')
            if idx is not None:
                if idx not in combined:
                    combined[idx] = result.copy()
                    combined[idx]['combined_score'] = 0.0
                # 키워드 점수를 정규화하여 추가
                keyword_score = result.get('keyword_score', 0)
                score = keyword_score / (keyword_score + 1) * 0.3
                combined[idx]['combined_score'] = combined[idx].get('combined_score', 0.0) + score
        
        # 점수 기준으로 정렬
        sorted_results = sorted(combined.values(), key=lambda x: x.get('combined_score', 0.0), reverse=True)
        
        return sorted_results[:top_k]
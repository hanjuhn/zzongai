"""
동요 Vector DB 로더 및 RAG 검색 모듈
"""
import pickle
import sys
from pathlib import Path
from typing import List, Dict, Any, Optional
import numpy as np
import faiss
import re
from collections import Counter

# 프로젝트 루트를 Python 경로에 추가
project_root = Path(__file__).parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))


class DongyoVectorDB:
    """동요 Vector DB 클래스"""
    
    def __init__(self, embeddings_path: str = None, index_path: str = None):
        """
        Vector DB 초기화
        
        Args:
            embeddings_path: embeddings pickle 파일 경로
            index_path: FAISS index 파일 경로
        """
        if embeddings_path is None:
            embeddings_path = project_root / "data" / "dongyo_embeddings.pkl"
        if index_path is None:
            index_path = project_root / "data" / "dongyo_faiss.index"
        
        self.embeddings_path = Path(embeddings_path)
        self.index_path = Path(index_path)
        
        # 데이터 로드
        self._load_data()
        
        # 키워드 검색을 위한 인덱스 구축 (비용 없음, 로컬 처리)
        self._build_keyword_index()
    
    def _load_data(self):
        """Vector DB 데이터 로드"""
        if not self.embeddings_path.exists():
            raise FileNotFoundError(f"Embeddings 파일을 찾을 수 없습니다: {self.embeddings_path}")
        if not self.index_path.exists():
            raise FileNotFoundError(f"FAISS index 파일을 찾을 수 없습니다: {self.index_path}")
        
        # 메타데이터 로드 (제목, 가사 특징 요약, 가사)
        with open(self.embeddings_path, "rb") as f:
            self.metadata = pickle.load(f)
        
        # FAISS index 로드
        self.index = faiss.read_index(str(self.index_path))
        
        # 동요 개수 계산 (딕셔너리 또는 리스트 형태 모두 지원)
        if isinstance(self.metadata, dict):
            song_count = len(self.metadata.get("titles", []))
        else:
            song_count = len(self.metadata)
        
        print(f"✅ Vector DB 로드 완료: {song_count}개 동요")
    
    def _build_keyword_index(self):
        """키워드 검색을 위한 인덱스 구축 (BM25 스타일)"""
        self.keyword_index = {}  # {keyword: [song_indices]}
        self.song_texts = []  # 각 동요의 검색 가능한 텍스트
        
        # 메타데이터에서 텍스트 추출
        if isinstance(self.metadata, dict):
            titles = self.metadata.get("titles", [])
            lyrics_list = self.metadata.get("lyrics", [])
            for i in range(len(titles)):
                title = titles[i] if i < len(titles) else ""
                lyrics = lyrics_list[i] if i < len(lyrics_list) else ""
                text = f"{title} {lyrics}".lower()
                self.song_texts.append(text)
        else:
            for i, meta in enumerate(self.metadata):
                title = meta.get("제목") if isinstance(meta, dict) else (meta.get("title") if isinstance(meta, dict) else "")
                lyrics = meta.get("가사") if isinstance(meta, dict) else (meta.get("lyrics") if isinstance(meta, dict) else "")
                feature = meta.get("가사 특징 요약") if isinstance(meta, dict) else (meta.get("feature_summary") if isinstance(meta, dict) else "")
                text = f"{title} {feature} {lyrics}".lower()
                self.song_texts.append(text)
        
        # 키워드 인덱스 구축 (간단한 역인덱스)
        for i, text in enumerate(self.song_texts):
            # 한국어와 영어 단어 추출
            words = re.findall(r'\b\w+\b', text)
            for word in words:
                if len(word) >= 2:  # 2글자 이상만 인덱싱
                    if word not in self.keyword_index:
                        self.keyword_index[word] = []
                    if i not in self.keyword_index[word]:
                        self.keyword_index[word].append(i)
    
    def search_similar(
        self, 
        query_embedding: np.ndarray, 
        top_k: int = 5
    ) -> List[Dict[str, Any]]:
        """
        유사한 동요 검색
        
        Args:
            query_embedding: 쿼리 임베딩 벡터
            top_k: 반환할 상위 k개 결과
            
        Returns:
            유사한 동요 정보 리스트 (제목, 가사 특징 요약, 가사 포함)
        """
        # query_embedding을 2D 배열로 변환 (1, dim)
        if query_embedding.ndim == 1:
            query_embedding = query_embedding.reshape(1, -1)
        
        # float32로 변환
        query_embedding = query_embedding.astype(np.float32)
        
        # FAISS 검색
        distances, indices = self.index.search(query_embedding, top_k)
        
        # 결과 구성
        results = []
        for i, idx in enumerate(indices[0]):
            # numpy 타입을 Python 기본 타입으로 변환
            try:
                if hasattr(idx, 'item'):
                    idx_int = int(idx.item())
                else:
                    idx_int = int(idx)
            except (ValueError, TypeError):
                idx_int = int(idx)
            
            # metadata가 딕셔너리인지 리스트인지 확인
            if isinstance(self.metadata, dict):
                # 딕셔너리 형태인 경우
                if idx_int < len(self.metadata.get("titles", [])):
                    titles = self.metadata.get("titles", [])
                    lyrics_list = self.metadata.get("lyrics", [])
                    title = titles[idx_int] if idx_int < len(titles) else ""
                    lyrics = lyrics_list[idx_int] if idx_int < len(lyrics_list) else ""
                    feature_summary = ""
                else:
                    continue
            else:
                # 리스트 형태인 경우
                if idx_int < len(self.metadata):
                    meta = self.metadata[idx_int]
                    # 다양한 키 이름 지원 (제목, 가사 특징 요약, 가사)
                    title = meta.get("제목") if isinstance(meta, dict) else (meta.get("title") if isinstance(meta, dict) else "")
                    feature_summary = meta.get("가사 특징 요약") if isinstance(meta, dict) else (meta.get("feature_summary") if isinstance(meta, dict) else (meta.get("특징") if isinstance(meta, dict) else ""))
                    lyrics = meta.get("가사") if isinstance(meta, dict) else (meta.get("lyrics") if isinstance(meta, dict) else "")
                else:
                    continue
            
            # numpy 타입을 Python 기본 타입으로 변환
            try:
                if hasattr(distances[0][i], 'item'):
                    distance_float = float(distances[0][i].item())
                else:
                    distance_float = float(distances[0][i])
            except (ValueError, TypeError):
                distance_float = float(distances[0][i])
            
            result = {
                "index": idx_int,
                "distance": distance_float,
                "title": str(title) if title else "",
                "feature_summary": str(feature_summary) if feature_summary else "",
                "lyrics": str(lyrics) if lyrics else "",
            }
            results.append(result)
        
        return results
    
    def search_by_keywords(
        self,
        keywords: List[str],
        top_k: int = 5
    ) -> List[Dict[str, Any]]:
        """
        키워드 기반 검색 (BM25 스타일, 비용 없음)
        
        Args:
            keywords: 검색할 키워드 리스트
            top_k: 반환할 상위 k개 결과
            
        Returns:
            검색된 동요 정보 리스트
        """
        if not keywords:
            return []
        
        # 키워드 점수 계산 (간단한 TF-IDF 스타일)
        scores = Counter()
        keywords_lower = [kw.lower() for kw in keywords]
        
        for keyword in keywords_lower:
            if keyword in self.keyword_index:
                # 키워드가 포함된 모든 동요에 점수 부여
                for song_idx in self.keyword_index[keyword]:
                    scores[song_idx] += 1
        
        # 상위 k개 선택
        top_indices = [idx for idx, _ in scores.most_common(top_k * 2)]  # 여유있게 2배 선택
        
        # 결과 구성
        results = []
        for idx in top_indices[:top_k]:
            score = scores[idx]
            
            # metadata에서 정보 추출
            if isinstance(self.metadata, dict):
                titles = self.metadata.get("titles", [])
                lyrics_list = self.metadata.get("lyrics", [])
                if idx < len(titles):
                    title = titles[idx]
                    lyrics = lyrics_list[idx] if idx < len(lyrics_list) else ""
                    feature_summary = ""
                else:
                    continue
            else:
                if idx < len(self.metadata):
                    meta = self.metadata[idx]
                    title = meta.get("제목") if isinstance(meta, dict) else (meta.get("title") if isinstance(meta, dict) else "")
                    feature_summary = meta.get("가사 특징 요약") if isinstance(meta, dict) else (meta.get("feature_summary") if isinstance(meta, dict) else (meta.get("특징") if isinstance(meta, dict) else ""))
                    lyrics = meta.get("가사") if isinstance(meta, dict) else (meta.get("lyrics") if isinstance(meta, dict) else "")
                else:
                    continue
            
            result = {
                "index": idx,
                "distance": 1.0 / (score + 1),  # 점수가 높을수록 distance는 낮음
                "keyword_score": score,
                "title": str(title) if title else "",
                "feature_summary": str(feature_summary) if feature_summary else "",
                "lyrics": str(lyrics) if lyrics else "",
            }
            results.append(result)
        
        return results
    
    def filter_by_categories(
        self,
        results: List[Dict[str, Any]],
        categories: Dict[str, str]
    ) -> List[Dict[str, Any]]:
        """
        카테고리 기반 필터링 (비용 없음)
        
        Args:
            results: 검색 결과 리스트
            categories: 필터링할 카테고리 (주제, 감정, 계절, 동물, 행동 등)
            
        Returns:
            필터링된 결과 리스트
        """
        if not categories or not any(categories.values()):
            return results  # 필터 조건이 없으면 원본 반환
        
        filtered = []
        category_keywords = []
        
        # 카테고리 키워드 추출
        for cat_type, cat_value in categories.items():
            if cat_value and cat_value.strip():
                category_keywords.append(cat_value.lower())
        
        if not category_keywords:
            return results
        
        # 각 결과에 대해 카테고리 키워드 매칭
        for result in results:
            # 제목, 특징, 가사에서 키워드 검색
            searchable_text = f"{result.get('title', '')} {result.get('feature_summary', '')} {result.get('lyrics', '')}".lower()
            
            # 카테고리 키워드 중 하나라도 매칭되면 포함
            matched = False
            for keyword in category_keywords:
                if keyword in searchable_text:
                    matched = True
                    break
            
            if matched:
                filtered.append(result)
        
        # 필터링 결과가 너무 적으면 원본 반환 (최소 1개는 보장)
        return filtered if len(filtered) >= 1 else results
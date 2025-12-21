"""
PDF 파일 처리 모듈
"""
import io
import sys
from typing import List, Optional

# 라이브러리 import 시도 (에러 메시지 개선)
PDFPLUMBER_AVAILABLE = False
PYPDF2_AVAILABLE = False
_import_errors = []

try:
    import pdfplumber
    PDFPLUMBER_AVAILABLE = True
except ImportError as e:
    _import_errors.append(f"pdfplumber: {str(e)}")

try:
    import PyPDF2
    PYPDF2_AVAILABLE = True
except ImportError as e:
    _import_errors.append(f"PyPDF2: {str(e)}")


def extract_text_from_pdf(pdf_bytes: bytes) -> str:
    """
    PDF 파일에서 텍스트를 추출합니다.
    pdfplumber를 우선 사용하고, 실패 시 PyPDF2를 사용합니다.
    """
    if not pdf_bytes or len(pdf_bytes) == 0:
        raise ValueError("PDF 파일이 비어있습니다.")
    
    # 라이브러리 확인
    if not PDFPLUMBER_AVAILABLE and not PYPDF2_AVAILABLE:
        error_msg = (
            "PDF 처리 라이브러리가 설치되지 않았습니다.\n"
            f"현재 Python 경로: {sys.executable}\n"
            f"현재 sys.path: {sys.path[:3]}...\n"
        )
        if _import_errors:
            error_msg += f"Import 오류:\n" + "\n".join(_import_errors) + "\n"
        error_msg += "다음 명령어로 설치해주세요:\n"
        error_msg += f"  {sys.executable} -m pip install pdfplumber PyPDF2"
        raise ImportError(error_msg)
    
    text_parts = []
    last_error = None
    
    # pdfplumber 시도 (더 정확함)
    if PDFPLUMBER_AVAILABLE:
        try:
            with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
                for page_num, page in enumerate(pdf.pages, 1):
                    try:
                        page_text = page.extract_text()
                        if page_text and page_text.strip():
                            text_parts.append(page_text.strip())
                    except Exception as e:
                        # 특정 페이지 추출 실패는 무시하고 계속 진행
                        continue
            if text_parts:
                return "\n\n".join(text_parts)
        except Exception as e:
            last_error = f"pdfplumber 오류: {str(e)}"
    
    # PyPDF2 폴백
    if PYPDF2_AVAILABLE:
        try:
            pdf_reader = PyPDF2.PdfReader(io.BytesIO(pdf_bytes))
            for page_num, page in enumerate(pdf_reader.pages, 1):
                try:
                    page_text = page.extract_text()
                    if page_text and page_text.strip():
                        text_parts.append(page_text.strip())
                except Exception as e:
                    # 특정 페이지 추출 실패는 무시하고 계속 진행
                    continue
            if text_parts:
                return "\n\n".join(text_parts)
        except Exception as e:
            if not last_error:
                last_error = f"PyPDF2 오류: {str(e)}"
    
    # 두 방법 모두 실패
    error_msg = "PDF에서 텍스트를 추출할 수 없습니다."
    if last_error:
        error_msg += f" ({last_error})"
    if not text_parts:
        error_msg += " PDF 파일이 텍스트를 포함하지 않거나 이미지로만 구성되어 있을 수 있습니다."
    
    raise RuntimeError(error_msg)


def is_pdf_file(filename: str) -> bool:
    """파일명이 PDF인지 확인"""
    return filename.lower().endswith('.pdf')


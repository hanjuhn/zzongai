# 학습용 멜로디 생성기

외우고 싶은 문장을 입력하거나, 이미지(최대 5장) 또는 PDF 파일을 업로드하여 기억하기 쉬운 멜로디와 함께 노래를 생성하는 에듀테크 웹 애플리케이션입니다.

## 주요 기능

- **텍스트 직접 입력**: 외우고 싶은 문장을 직접 입력 (최대 300자)
- **다중 이미지 업로드**: 최대 5장의 이미지를 업로드하여 종합 분석
- **PDF 파일 지원**: PDF 파일에서 텍스트 추출 및 학습 자료 생성
- **이미지 타입별 분석**:
  - 텍스트 이미지: OCR을 통한 텍스트 추출
  - 수식 이미지: 수식을 음으로 표현 가능한 형태로 변환
  - 지도 이미지: 관련 역사/지리 정보를 요약하여 가사 생성
  - 다이어그램/차트: 학습용 요약 생성
- **자동 종합 및 요약**: 여러 파일의 내용을 종합하여 일관된 학습 자료로 정리
- **멜로디 가이드 생성**: 학습 텍스트를 기억하기 쉬운 멜로디 가이드로 변환
- **노래 생성**: Suno API를 사용하여 실제 노래 생성

## 설치

### 0. Docker로 실행 (권장)

Docker를 사용하면 환경 설정 없이 바로 실행할 수 있습니다.

#### Docker 이미지 빌드

```bash
docker build -t melody-learning:latest .
```

#### Docker 컨테이너 실행

```bash
docker run -p 8000:8000 \
  -e OPENAI_API_KEY=your_openai_api_key_here \
  -e SUNO_API_KEY=your_suno_api_key_here \
  -v $(pwd)/data:/app/data \
  melody-learning:latest
```

또는 `.env` 파일을 사용:

```bash
docker run -p 8000:8000 \
  --env-file .env \
  -v $(pwd)/data:/app/data \
  melody-learning:latest
```

**참고**: 
- `-v $(pwd)/data:/app/data`: 벡터 DB 데이터 파일을 마운트 (선택사항)
- 브라우저에서 `http://localhost:8000` 접속

### CI/CD 파이프라인

이 프로젝트는 GitHub Actions를 사용한 CI/CD 파이프라인이 설정되어 있습니다.

#### 자동 검증 항목

코드를 GitHub에 푸시하면 자동으로 다음 검증이 실행됩니다:

1. **코드 검증**
   - Python 문법 검사
   - Import 검사
   - 코드 포맷팅 검사 (Black)
   - 린터 검사 (Flake8)

2. **Docker 빌드 테스트**
   - Docker 이미지 빌드 성공 여부 확인
   - 이미지 내부 검증

3. **서버 시작 테스트**
   - FastAPI 서버가 정상적으로 시작되는지 확인
   - 헬스 체크 엔드포인트 검증

#### CI/CD 워크플로우 확인

GitHub 저장소의 **Actions** 탭에서 CI/CD 실행 상태를 확인할 수 있습니다:
- ✅ 초록색: 모든 검증 통과
- ❌ 빨간색: 검증 실패 (코드 수정 필요)
- 🟡 노란색: 실행 중

#### 자동 배포

- **main 브랜치**에 푸시하면 자동으로 배포 준비가 완료됩니다
- Railway가 GitHub과 연결되어 있으면 자동 배포가 시작됩니다
- Railway 대시보드에서 "Auto Deploy" 설정을 활성화하세요

#### 수동 실행

GitHub Actions 탭에서 "Run workflow" 버튼을 클릭하여 수동으로 CI/CD를 실행할 수 있습니다.

### 1. 의존성 설치 (로컬 실행)

```bash
pip install -r requirements.txt
```

필요한 라이브러리:
- `fastapi`: 웹 프레임워크
- `uvicorn`: ASGI 서버
- `python-dotenv`: 환경 변수 관리
- `openai`: OpenAI API 클라이언트
- `requests`: HTTP 요청
- `pydantic`: 데이터 검증
- `python-multipart`: 파일 업로드 처리
- `PyPDF2`: PDF 처리
- `pdfplumber`: PDF 처리 (더 정확함)

### 2. 환경 변수 설정

프로젝트 루트에 `.env` 파일을 만들고 다음 내용을 추가하세요:

```env
OPENAI_API_KEY=your_openai_api_key_here
SUNO_API_KEY=your_suno_api_key_here
SUNO_CALLBACK_URL=https://httpbin.org/post  # 선택사항
```

**API 키 발급 방법:**
- **OpenAI API 키**: https://platform.openai.com/api-keys 에서 발급
- **Suno API 키**: https://api.sunoapi.org 에서 발급

## 실행 방법

### 웹 애플리케이션 실행

#### 1. 백엔드 서버 시작

터미널 1에서:

```bash
cd /Users/chloe/Downloads/melody-learning-main
uvicorn src.server:app --reload --host 0.0.0.0 --port 8000
```

백엔드가 `http://localhost:8000`에서 실행됩니다.

#### 2. 브라우저에서 접속

브라우저에서 `http://localhost:8000`을 열고 사용하세요.

**참고**: FastAPI 서버가 프론트엔드도 함께 서빙하므로 별도의 프론트엔드 서버를 실행할 필요가 없습니다.

### 사용 방법

#### 방법 1: 텍스트 직접 입력
1. "외우고 싶은 문장 입력" 텍스트 영역에 내용을 입력 (최대 300자)
2. "멜로디 생성" 버튼 클릭

#### 방법 2: 이미지 업로드
1. "파일 업로드"에서 이미지 파일 선택 (최대 5장)
2. 지원되는 이미지 타입:
   - 텍스트가 포함된 이미지: 텍스트 추출
   - 수식 이미지: 수식을 음으로 표현 가능한 형태로 변환
   - 지도 이미지: 관련 역사/지리 정보 요약
   - 다이어그램/차트: 학습용 요약
3. "멜로디 생성" 버튼 클릭

#### 방법 3: PDF 파일 업로드
1. "파일 업로드"에서 PDF 파일 선택 (최대 1개)
2. PDF에서 텍스트가 자동으로 추출됩니다
3. "멜로디 생성" 버튼 클릭

#### 방법 4: 조합 사용
- 텍스트 입력 + 이미지 업로드
- 이미지 여러 장 + PDF
- 등등 자유롭게 조합 가능

### CLI로 실행

이미지 파일 경로를 직접 지정해서 실행할 수 있습니다:

```bash
python3 src/run_pipeline.py <이미지_경로>
```

예시:

```bash
python3 src/run_pipeline.py /path/to/image.png
```

### 웹사이트로 실행
아래 URL에 접속하여 웹 서비스를 이용할 수 있습니다.
https://melodytest-production.up.railway.app/

## 프로젝트 구조

```
melody-learning-main/
├── src/
│   ├── server.py              # FastAPI 백엔드 (웹용)
│   ├── run_pipeline.py        # CLI 파이프라인
│   ├── suno_client.py         # Suno API 클라이언트
│   ├── image_analyzer.py       # 이미지 타입별 분석
│   ├── pdf_processor.py       # PDF 처리 모듈
│   ├── core/
│   │   ├── workflow.py         # 핵심 워크플로우 함수들
│   │   └── mureka_utils.py     # 오디오 처리 유틸
│   ├── agents.py               # 멜로디 가이드 생성
│   ├── compose_prompt.py       # Suno 페이로드 구성
│   └── vision_to_query.py     # 이미지 OCR
│
├── web/
│   ├── index.html             # 프론트엔드 HTML
│   └── main.js                # 순수 JavaScript
│
├── requirements.txt           # Python 의존성
└── README.md                  # 이 파일
```

## API 엔드포인트

- `POST /extract-text`: 이미지(base64)에서 텍스트 추출
- `POST /extract-from-files`: 다중 파일(이미지/PDF)에서 텍스트 추출 및 종합
- `POST /mnemonic-plan`: 학습 텍스트로 멜로디 가이드 생성
- `POST /generate-lyrics`: 학습 텍스트로 가사만 생성
- `POST /generate-song`: Suno API로 노래 생성
- `GET /health`: 헬스 체크
- `GET /docs`: API 문서 (Swagger UI)

## 문제 해결

### PDF 처리 오류

**에러 메시지**: "PDF 처리 라이브러리가 설치되지 않았습니다"

**해결 방법**:
```bash
pip install pdfplumber PyPDF2
```

설치 후 서버를 재시작하세요.

### Suno API 오류

**에러 메시지**: "Please enter callBackUrl"

이미 해결되었습니다. `callBackUrl`이 자동으로 설정됩니다.

### 429 Too Many Requests 오류

Suno API의 요청 제한에 걸렸을 수 있습니다. 잠시 기다렸다가 다시 시도하세요.

### 모듈을 찾을 수 없다는 오류

프로젝트 루트에서 실행했는지 확인하세요. `PYTHONPATH`가 필요할 수 있습니다:

```bash
export PYTHONPATH=/Users/chloe/Downloads/melody-learning-main:$PYTHONPATH
```

### 이미지에서 텍스트를 추출하지 못함

- 이미지가 텍스트를 포함하고 있는지 확인
- 이미지 파일 형식이 지원되는지 확인 (PNG, JPEG)
- 이미지가 손상되지 않았는지 확인

### PDF에서 텍스트를 추출하지 못함

- PDF가 텍스트를 포함하고 있는지 확인 (이미지만 있는 PDF는 처리 불가)
- PDF 파일이 손상되지 않았는지 확인
- PDF 라이브러리가 설치되어 있는지 확인

## 기술 스택

- **백엔드**: FastAPI, Python
- **프론트엔드**: 순수 JavaScript (Vanilla JS)
- **AI/ML**: OpenAI GPT-4o-mini (Vision API)
- **음악 생성**: Suno API
- **PDF 처리**: pdfplumber, PyPDF2

## 라이선스

이 프로젝트는 MIT 라이선스를 따릅니다.

"""
Semantic Search & Retrieval Pipeline for RAG (Retrieval-Augmented Generation) System

이 스크립트는 사용자의 질문(Query)을 받아 다음의 과정을 수행합니다:
1. 용어 사전(tax_glossary.csv)을 이용한 질의 확장 (Query Expansion)
2. Qdrant 벡터 DB를 검색하여 관련성이 높은 문서 청크(Chunk) 추출
3. AI 라우터(GPT-4o)를 활용하여 추출된 문서의 문맥에 맞는 최적의 URL 매핑 (및 Fallback 처리)
4. LLM(GPT-4o)을 통한 최종 자연어 답변(Answer) 생성

생성된 답변과 함께 출처(Sources) 정보(제목, 원문, 추천 링크)를 JSON 형태로 반환하며,
이는 FastAPI 엔드포인트를 통해 프론트엔드로 전달됩니다.
"""

import os
import json
from datetime import datetime
from typing import List, Dict, Any

import pandas as pd
from dotenv import load_dotenv

from qdrant_client import QdrantClient
from sentence_transformers import SentenceTransformer
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

# =====================================================================
# 1. Global Configurations & Environment Setup (전역 설정)
# =====================================================================
# .env 파일 로드 (API 키 보안 유지)
load_dotenv()  

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, 'data')
DB_DIR = os.path.join(BASE_DIR, 'qdrant_db_local')

COLLECTION_NAME = "tax_youth_policy"
EMBEDDING_MODEL_NAME = 'BAAI/bge-m3'
LLM_MODEL_NAME = "gpt-4o"

# =====================================================================
# 2. Resource Initialization (리소스 로드 - 서버 기동 시 1회 실행)
# =====================================================================

def _load_tax_glossary() -> Dict[str, str]:
    """세무 용어 사전을 로드하여 순화어-전문용어 매핑 딕셔너리를 반환합니다."""
    glossary_path = os.path.join(DATA_DIR, 'tax_glossary.csv')
    try:
        df_glossary = pd.read_csv(glossary_path)
        # 결측치(NaN)가 문자열 처리되는 것을 방지하기 위한 필터링
        easy_to_term = {
            str(row['순화어']): str(row['용어']) 
            for _, row in df_glossary.iterrows() 
            if pd.notna(row['순화어']) and pd.notna(row['용어'])
        }
        print(f"[INFO] 세무 용어 사전 로드 완료 ({len(easy_to_term)}개 항목).")
        return easy_to_term
    except FileNotFoundError:
        print(f"[WARNING] '{glossary_path}' 파일을 찾을 수 없어 용어 확장을 건너뜁니다.")
        return {}
    except Exception as e:
        print(f"[ERROR] 용어 사전 로드 중 오류 발생: {e}")
        return {}

def _load_source_links() -> Dict[str, List[str]]:
    """문맥 기반 URL 매핑을 위한 출처 링크 JSON 파일을 로드합니다."""
    source_links_path = os.path.join(DATA_DIR, 'source_links.json')
    try:
        with open(source_links_path, "r", encoding="utf-8") as f:
            links_map = json.load(f)
            print(f"[INFO] 출처 링크 맵 로드 완료 ({len(links_map)}개 키워드).")
            return links_map
    except FileNotFoundError:
        print(f"[WARNING] '{source_links_path}' 파일을 찾을 수 없습니다. 빈 맵을 사용합니다.")
        return {}
    except json.JSONDecodeError:
         print(f"[ERROR] '{source_links_path}' 파일의 JSON 형식이 올바르지 않습니다.")
         return {}

# 💡 서버 메모리에 상주할 글로벌 리소스 초기화 (Dependency Injection)
EASY_TO_TERM_MAP = _load_tax_glossary()
SOURCE_INFO_MAP = _load_source_links()

print(f"[INFO] 임베딩 모델 '{EMBEDDING_MODEL_NAME}' 로딩 중...")
embed_model = SentenceTransformer(EMBEDDING_MODEL_NAME)
qdrant_client = QdrantClient(path=DB_DIR)

llm = ChatOpenAI(temperature=0, model_name=LLM_MODEL_NAME)


# =====================================================================
# 3. Prompts Definition (프롬프트 정의)
# =====================================================================

# 최종 자연어 답변 생성을 위한 LLM 프롬프트
ANSWER_PROMPT = ChatPromptTemplate.from_template("""
당신은 청년들을 위한 친절하고 전문적인 세무/정책 가이드입니다.
아래 제공된 [관련 문서]만을 바탕으로 사용자의 [질문]에 답변하세요.

<규칙>
1. 제공된 문서에 없는 내용은 절대 지어내지 마세요.
2. 행정/세무 용어는 일상어로 쉽게 풀어서 설명하세요.
3. 답변 하단에 반드시 근거가 된 [출처]를 명시하세요.

[관련 문서]
{context}

[질문]
{question}
""")

# URL 매핑을 위한 AI 라우터 프롬프트 (JSON 배열 강제 출력)
URL_ROUTER_PROMPT = ChatPromptTemplate.from_template("""
당신은 텍스트의 문맥을 깊이 분석하여 가장 적절한 URL과 제목을 매핑하는 최고 수준의 데이터 라우터입니다.
아래 [참조 문서]를 읽고, [https://dict.naver.com/에서](https://dict.naver.com/에서) 문맥상 가장 연관성이 높은 항목을 찾아내세요.

<핵심 규칙>
1. 무조건 1개 이상의 링크를 찾아야 합니다. (관련 정책이나 주관 기관을 유추하여 선택하세요.)
2. 반드시 다음과 같은 유효한 JSON 배열 형식으로만 출력하세요: [{{"title": "사전에 적힌 키워드명", "url": "해당 URL"}}]
3. 마크다운 기호(```json 등)나 부가 설명은 절대 포함하지 마세요.

[참조 문서]
주제: {topic}
출처: {source}
내용: {content}

https://dict.naver.com/
{url_dict}
""")

URL_ROUTER_CHAIN = URL_ROUTER_PROMPT | llm | StrOutputParser()


# =====================================================================
# 4. Core Business Logic (핵심 검색 및 생성 로직)
# =====================================================================

def _expand_query(user_query: str) -> str:
    """
    사용자의 질문에 포함된 순화어를 전문 용어로 확장하여 벡터 검색의 정확도를 높입니다.
    """
    expanded_query = user_query
    for easy_word, technical_term in EASY_TO_TERM_MAP.items():
        if easy_word in user_query:
            expanded_query += f" {technical_term}"
    return expanded_query


def _get_fallback_links(topic_text: str) -> List[Dict[str, str]]:
    """
    AI 라우터가 적절한 링크를 찾지 못했을 때(오류 또는 빈 결과),
    텍스트의 주요 키워드를 분석하여 최소 1개 이상의 기본(Fallback) 링크를 보장합니다.
    """
    # 1순위: 주거/월세/주택 관련
    if any(keyword in topic_text for keyword in ["월세", "주거", "전세", "주택", "임차"]):
        return [{"title": "마이홈포털 (주거/월세 정책)", "url": "https://www.myhome.go.kr"}]
    
    # 2순위: 금융/자산/적금 관련
    if any(keyword in topic_text for keyword in ["적금", "도약계좌", "자산", "저축"]):
        return [{"title": "서민금융진흥원 (청년자산형성)", "url": "https://ylaccount.kinfa.or.kr"}]
    
    # 3순위: 연말정산이나 세금/소득 관련
    if any(keyword in topic_text for keyword in ["연말정산", "세금", "소득", "공제"]):
        return [{"title": "국세청 (연말정산/소득공제 안내)", "url": "https://www.nts.go.kr/nts/cm/cntnts/cntntsView.do?cntntsId=238910&mi=40296"}]
    
    # 4순위: 그 외의 경우 복지로 포털 반환
    return [{"title": "복지로 (청년 맞춤형 복지)", "url": "https://www.bokjiro.go.kr"}]


def get_answer_with_sources(user_query: str) -> Dict[str, Any]:
    """
    주어진 질문에 대한 AI 답변과 참고한 출처(URL 포함)를 생성하여 반환합니다.
    (⚠️ FastAPI 엔드포인트에서 호출되므로 리턴 구조를 변경하지 마세요.)
    
    Args:
        user_query (str): 사용자의 원본 질문

    Returns:
        Dict[str, Any]: {
            "answer": str,       # LLM이 생성한 최종 텍스트 답변
            "sources": List[...] # 출처 주제, 내용, 추천 링크(links) 객체 리스트
        }
    """
    # 1. 쿼리 확장 및 Vector DB 검색
    expanded_query = _expand_query(user_query)
    query_vector = embed_model.encode(expanded_query).tolist()
    
    search_results = qdrant_client.query_points(
        collection_name=COLLECTION_NAME,
        query=query_vector,
        limit=3 
    ).points

    sources_list = []
    context_str = ""
    
    # 2. 검색 결과 분석 및 동적 URL 라우팅 (AI 기반)
    for res in search_results:
        payload = res.payload or {}
        
        raw_source_text = payload.get('source', '공공 세무/정책 데이터베이스')
        topic_text = payload.get('topic', '')
        content_text = payload.get('content', '')
        
        # 🤖 AI를 활용하여 문맥에 가장 적합한 {title, url} 쌍 추출
        try:
            ai_selected_str = URL_ROUTER_CHAIN.invoke({
                "topic": topic_text,
                "source": raw_source_text,
                "content": content_text,
                "url_dict": json.dumps(SOURCE_INFO_MAP, ensure_ascii=False)
            })
            
            # Markdown 기호 방어 코드 및 JSON 파싱
            cleaned_str = ai_selected_str.replace("```json", "").replace("```", "").strip()
            best_matched_links = json.loads(cleaned_str)
            
            if not isinstance(best_matched_links, list):
                best_matched_links = []
                
        except Exception as e:
            print(f"[WARNING] URL 매칭 중 오류 발생 (Fallback 진행): {e}")
            best_matched_links = []

        # 🛡️ 3. Fallback 처리: 빈 배열인 경우 무조건 1개 이상의 링크 강제 주입
        if not best_matched_links:
            best_matched_links = _get_fallback_links(topic_text)

        # 4. 결과 리스트에 출처 정보 및 구조화된 링크 적재
        sources_list.append({
            "주제": topic_text,
            "출처파일명": raw_source_text, 
            "links": best_matched_links,
            "원문내용": content_text
        })
        
        # LLM에게 제공할 컨텍스트 텍스트 누적
        context_str += f"[출처: {raw_source_text} - {topic_text}]\n{content_text}\n\n"

    # 5. 최종 LLM 답변 생성
    answer_chain = ANSWER_PROMPT | llm | StrOutputParser()
    answer = answer_chain.invoke({
        "context": context_str, 
        "question": user_query
    })

    return {
        "answer": answer,
        "sources": sources_list
    }


# =====================================================================
# 5. Testing & Execution (독립 실행 시 테스트)
# =====================================================================

def _get_current_time_str() -> str:
    """로깅용 현재 시간 문자열 반환"""
    return f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]}]"

def test_main():
    """스크립트 단독 실행 시 파이프라인의 정상 작동을 테스트합니다."""
    print(f"{_get_current_time_str()} [INFO] 테스트 환경 기동...")

    test_queries = [
        "월세 지원금 받으려면 전입신고 꼭 해야해?",
        "신용카드로 쓴 돈은 무조건 다 소득공제 돼?",
        "토스 뱅크 청년미래적금 vs 청년도약계좌 알려줘"
    ]
    
    for query in test_queries:
        print(f"\n🗣️ 사용자 질문: {query}")
        try:
            result = get_answer_with_sources(query)
            print(f"💡 AI 답변:\n{result['answer']}")
            print(f"📚 참조 출처 개수: {len(result['sources'])}개")
            for i, src in enumerate(result['sources']):
                print(f"  [{i+1}] {src['주제']} (링크 {len(src['links'])}개)")
        except Exception as e:
            print(f"[ERROR] 질의 처리 중 오류: {e}")
        print("-" * 50)

    print(f"{_get_current_time_str()} [INFO] 테스트 종료.")


if __name__ == "__main__":
    start_time = datetime.now()
    test_main()
    finish_time = datetime.now()
    print(f"{_get_current_time_str()} [INFO] 전체 소요 시간: {(finish_time-start_time).total_seconds():.2f}s")
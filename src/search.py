from datetime import datetime
import os
import pandas as pd
from qdrant_client import QdrantClient
from sentence_transformers import SentenceTransformer
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

open_api_key = "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"

##### 전역 설정 (API 서버 연동 및 즉시 로딩을 위해 전역 유지)
os.environ["OPENAI_API_KEY"] = open_api_key 

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, 'data')
DB_DIR = os.path.join(BASE_DIR, 'qdrant_db_local')

##### 1. 세무 용어 사전 로드 (Query Expansion 용)
df_glossary = pd.read_csv(os.path.join(DATA_DIR, 'tax_glossary.csv'))
easy_to_term = dict(zip(df_glossary['순화어'], df_glossary['용어']))

##### 2. 임베딩 모델 및 Qdrant DB 연결
print("BGE-M3 모델 로딩 중...")
embed_model = SentenceTransformer('BAAI/bge-m3')
qdrant_client = QdrantClient(path=DB_DIR)
collection_name = "tax_youth_policy"

##### 3. LLM 세팅 (GPT-4o) 및 프롬프트 템플릿 설계
llm = ChatOpenAI(
    temperature=0,
    model_name="gpt-4o"
)

prompt = ChatPromptTemplate.from_template("""
당신은 청년들을 위한 친절하고 전문적인 세무/정책 가이드 '라마'입니다.
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


def mainStart():
    print(getCurrentTimeStr(), "mainStart() is started...")

    ##### 프로세스 1 - 질의 확장 및 테스트 실행
    test_queries = [
        "가족 기업 물려받기 하려면 조건이 뭐야?",
        "월세 지원금 받으려면 전입신고 꼭 해야해?",
        "신용카드로 쓴 돈은 무조건 다 소득공제 돼?"
    ]
    
    for query in test_queries:
        print(f"🗣️ 사용자 질문: {query}")
        result = get_answer_with_sources(query)
        print(f"💡 AI 답변:\n{result['answer']}")
        print(f"📚 참조 출처 개수: {len(result['sources'])}개")
        print("-" * 50)

    print(getCurrentTimeStr(), "mainStart() is finished...")


def expand_query(user_query: str) -> str:
    """사용자 질문에 순화어가 있으면 전문 용어를 덧붙여 검색 퀄리티를 높임"""
    expanded_query = user_query
    for easy, term in easy_to_term.items():
        if str(easy) in user_query and str(easy) != 'nan':
            expanded_query += f" {term}"
    return expanded_query


# ==========================================
# 보안 및 UI 개선용 파일명 매핑 딕셔너리 추가
# ==========================================
FILE_NAME_MAP = {
    "yearend_tax_rag_data_v3.json": "국세청 연말정산 기본 안내",
    "yearend_tax_rag_supplementary.json": "국세청 연말정산 추가 지침서",
    "youth_housing_welfare_rag_v2.json": "청년 주거복지 정책 가이드"
}

def get_answer_with_sources(user_query: str):
    ##### 1. 쿼리 확장 및 벡터 DB 검색
    expanded_query = expand_query(user_query)
    query_vector = embed_model.encode(expanded_query).tolist()
    search_results = qdrant_client.query_points(
        collection_name=collection_name,
        query=query_vector,
        limit=3 
    ).points

    ##### 2. 검색 결과(출처)를 사전(JSON) 형태로 정리
    sources_list = []
    context_str = ""
    for res in search_results:
        payload = res.payload
        raw_filename = payload.get('source_file')
        
        # 🛡️ 핵심: 실제 파일명 대신 깔끔한 공식 명칭으로 변환 (사전에 없으면 기본값 사용)
        safe_filename = FILE_NAME_MAP.get(raw_filename, "공공 세무/정책 데이터베이스")

        # 프론트엔드에 보낼 데이터
        sources_list.append({
            "주제": payload.get('topic'),
            "출처파일명": safe_filename, # 변환된 안전한 이름 사용
            "원문내용": payload.get('content')
        })
        # LLM에게 줄 텍스트 데이터 (LLM에게도 파일명 대신 안전한 이름 제공)
        context_str += f"[출처: {safe_filename} - {payload.get('topic')}]\n{payload.get('content')}\n\n"

    ##### 3. LCEL을 이용한 체인 생성 및 LLM 답변 추출
    chain = prompt | llm | StrOutputParser()
    answer = chain.invoke({"context": context_str, "question": user_query})

    ##### 4. 정답과 출처 데이터를 한 번에 반환
    return {
        "answer": answer,
        "sources": sources_list
    }

def getCurrentTimeStr():
    currentTimeStr = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
    return f"[{currentTimeStr}]"

if __name__ == "__main__":

    start_time = datetime.now()
    print(getCurrentTimeStr(), "main Start..")
    #############

    mainStart()

    #############
    finish_time = datetime.now()
    print(getCurrentTimeStr(), f"main Finish..({(finish_time-start_time).total_seconds()}s Elapsed)")
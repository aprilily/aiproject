from datetime import datetime
import os
import pandas as pd
import json
import ast
from qdrant_client import QdrantClient
from sentence_transformers import SentenceTransformer
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

# .env 파일 로드 (이 코드가 API 키를 안전하게 불러옵니다)
load_dotenv()

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, 'data')
DB_DIR = os.path.join(BASE_DIR, 'qdrant_db_local')

##### 1. 세무 용어 사전 로드 (Query Expansion 용)
try:
    df_glossary = pd.read_csv(os.path.join(DATA_DIR, 'tax_glossary.csv'))
    easy_to_term = dict(zip(df_glossary['순화어'], df_glossary['용어']))
except FileNotFoundError:
    print("⚠️ tax_glossary.csv 파일을 찾을 수 없어 용어 확장을 건너뜁니다.")
    easy_to_term = {}

##### 2. 출처 링크 JSON 로드 (안전한 절대 경로 사용 및 예외 처리)
source_links_path = os.path.join(DATA_DIR, 'source_links.json')
try:
    with open(source_links_path, "r", encoding="utf-8") as f:
        SOURCE_INFO_MAP = json.load(f)
except FileNotFoundError:
    print(f"⚠️ {source_links_path} 파일을 찾을 수 없습니다. 빈 링크 맵을 사용합니다.")
    SOURCE_INFO_MAP = {}

##### 3. 임베딩 모델 및 Qdrant DB 연결
print("BGE-M3 모델 로딩 중...")
embed_model = SentenceTransformer('BAAI/bge-m3')
qdrant_client = QdrantClient(path=DB_DIR)
collection_name = "tax_youth_policy"

##### 4. LLM 세팅 (GPT-4o) 및 프롬프트 템플릿 설계
llm = ChatOpenAI(
    temperature=0,
    model_name="gpt-4o"
)

prompt = ChatPromptTemplate.from_template("""
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


def expand_query(user_query: str) -> str:
    """사용자 질문에 순화어가 있으면 전문 용어를 덧붙여 검색 퀄리티를 높임"""
    expanded_query = user_query
    for easy, term in easy_to_term.items():
        if str(easy) in user_query and str(easy) != 'nan':
            expanded_query += f" {term}"
    return expanded_query

def get_answer_with_sources(user_query: str):
    ##### 1. 쿼리 확장 및 벡터 DB 검색
    expanded_query = expand_query(user_query)
    query_vector = embed_model.encode(expanded_query).tolist()
    search_results = qdrant_client.query_points(
        collection_name=collection_name,
        query=query_vector,
        limit=3 
    ).points

    # 🤖 1. AI 라우터 프롬프트 강화 (정확도 상승 및 1개 이상 강제)
    url_router_prompt = ChatPromptTemplate.from_template("""
    당신은 텍스트의 문맥을 깊이 분석하여 가장 적절한 URL과 제목을 매핑하는 최고 수준의 데이터 라우터입니다.
    아래 [참조 문서]를 읽고, https://dict.naver.com/에서 문맥상 가장 연관성이 높은 항목을 찾아내세요.

    <핵심 규칙>
    1. 무조건 1개 이상의 링크를 찾아야 합니다. (문서에 직접적인 단어가 없더라도, 내용(예: 세금, 주거, 적금 등)을 바탕으로 가장 관련 깊은 정책이나 주관 기관을 유추하여 무조건 선택하세요.)
    2. 반드시 다음과 같은 유효한 JSON 배열 형식으로만 출력하세요: [{{"title": "사전에 적힌 키워드명", "url": "해당 URL"}}]
    3. 마크다운 기호(```json 등)나 부가 설명은 절대 포함하지 마세요.

    [참조 문서]
    주제: {topic}
    출처: {source}
    내용: {content}

    [https://dict.naver.com/](https://dict.naver.com/)
    {url_dict}
    """)
    url_chain = url_router_prompt | llm | StrOutputParser()

    ##### 2. 검색 결과(출처)를 사전 형태로 정리
    sources_list = []
    context_str = ""
    for res in search_results:
        payload = res.payload
        
        raw_source_text = payload.get('source', '공공 세무/정책 데이터베이스')
        topic_text = payload.get('topic', '')
        content_text = payload.get('content', '')
        
        try:
            ai_selected_str = url_chain.invoke({
                "topic": topic_text,
                "source": raw_source_text,
                "content": content_text,
                "url_dict": json.dumps(SOURCE_INFO_MAP, ensure_ascii=False)
            })
            
            cleaned_str = ai_selected_str.replace("```json", "").replace("```", "").strip()
            best_matched_links = json.loads(cleaned_str)
            
            if not isinstance(best_matched_links, list):
                best_matched_links = []
                
        except Exception as e:
            print(f"⚠️ URL 매칭 중 오류 발생: {e}")
            best_matched_links = []

        # 🛡️ 2. Fallback: AI가 실패하거나 빈 배열을 주면 무조건 1개 강제 할당
        if len(best_matched_links) == 0:
            # 1순위: 주거/월세/주택 관련 내용인지 먼저 확인
            if "월세" in topic_text or "주거" in topic_text or "전세" in topic_text or "주택" in topic_text or "임차" in topic_text:
                best_matched_links = [{"title": "마이홈포털 (주거/월세 정책)", "url": "https://www.myhome.go.kr"}]
            # 2순위: 금융/자산/적금 관련 내용인지 확인
            elif "적금" in topic_text or "도약계좌" in topic_text or "자산" in topic_text or "저축" in topic_text:
                best_matched_links = [{"title": "서민금융진흥원 (청년자산형성)", "url": "https://ylaccount.kinfa.or.kr"}]
            # 3순위: 위 두 개가 아니면, 연말정산이나 세금/소득 관련 내용으로 처리
            elif "연말정산" in topic_text or "세금" in topic_text or "소득" in topic_text or "공제" in topic_text:
                best_matched_links = [{"title": "국세청 (연말정산/소득공제 안내)", "url": "https://www.nts.go.kr/nts/cm/cntnts/cntntsView.do?cntntsId=238910&mi=40296"}]
            # 4순위: 그래도 모르겠으면 만능 복지 포털로 보냄
            else:
                best_matched_links = [{"title": "복지로 (청년 맞춤형 복지)", "url": "https://www.bokjiro.go.kr"}]

        sources_list.append({
            "주제": topic_text,
            "출처파일명": raw_source_text, 
            "links": best_matched_links, # 무조건 1개 이상의 링크가 담겨있음이 보장됨!
            "원문내용": content_text
        })
        
        context_str += f"[출처: {raw_source_text} - {topic_text}]\n{content_text}\n\n"

    ##### 3. LCEL을 이용한 체인 생성 및 최종 LLM 답변 추출
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


def mainStart():
    print(getCurrentTimeStr(), "mainStart() is started...")

    ##### 프로세스 1 - 질의 확장 및 테스트 실행
    test_queries = [
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


if __name__ == "__main__":
    start_time = datetime.now()
    print(getCurrentTimeStr(), "main Start..")
    #############

    mainStart()

    #############
    finish_time = datetime.now()
    print(getCurrentTimeStr(), f"main Finish..({(finish_time-start_time).total_seconds()}s Elapsed)")
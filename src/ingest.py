import json
import uuid
import hashlib
import os
from qdrant_client import QdrantClient
from qdrant_client.models import VectorParams, Distance, PointStruct
from sentence_transformers import SentenceTransformer

# 0. 경로 설정 (src 폴더에서 실행한다고 가정)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__))) # my_rag_project 최상위 경로
DATA_DIR = os.path.join(BASE_DIR, 'data')
DB_DIR = os.path.join(BASE_DIR, 'qdrant_db_local')

# 1. Qdrant 클라이언트 연결 (로컬 환경)
client = QdrantClient(path=DB_DIR)
collection_name = "tax_youth_policy"

# 2. 임베딩 모델 로드
print("BGE-M3 모델 로딩 중...")
model = SentenceTransformer('BAAI/bge-m3')
vector_size = model.get_sentence_embedding_dimension() # 1024차원

# 3. 컬렉션 생성 (기존에 없으면 생성)
if not client.collection_exists(collection_name):
    client.create_collection(
        collection_name=collection_name,
        vectors_config=VectorParams(size=vector_size, distance=Distance.COSINE),
    )
    print(f"'{collection_name}' 컬렉션 생성 완료.")

# 4. 적재할 JSON 파일 목록 (data 폴더 내)
json_files = [
    'yearend_tax_rag_data_v3.json',
    'yearend_tax_rag_supplementary.json',
    'youth_housing_welfare_rag_v2.json',
    'youth_asset_job_policy_rag_2026_v3.json',
    'youth_rent_support_rag_2026_v2.json'
]

# 5. 모든 파일의 데이터 읽어오기
all_docs = []
for filename in json_files:
    file_path = os.path.join(DATA_DIR, filename)
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            docs = json.load(f)
            # 출처 식별을 위해 메타데이터에 파일명 추가
            for doc in docs:
                doc['source_file'] = filename 
            all_docs.extend(docs)
            print(f"'{filename}' 에서 {len(docs)}개 청크 로드 완료.")
    except FileNotFoundError:
        print(f"경고: '{file_path}' 파일을 찾을 수 없습니다. 건너뜁니다.")
    except json.JSONDecodeError:
         print(f"경고: '{file_path}' 파일 형식이 올바르지 않습니다.")

# 문자열 ID(예: "H001")를 Qdrant용 UUID로 변환하는 함수
def generate_uuid(string_id):
    hash_obj = hashlib.md5(string_id.encode('utf-8'))
    return str(uuid.UUID(hash_obj.hexdigest()))

# 6. 임베딩 추출 및 Qdrant 적재
print("\n데이터 임베딩 및 적재 시작 (시간이 약간 소요될 수 있습니다)...")
points = []

for doc in all_docs:
    # 텍스트를 BGE-M3 모델을 통해 1024차원 벡터로 변환
    vector = model.encode(doc["content"]).tolist()
    
    # "H001", "T065" 등의 ID를 UUID 형식으로 변환
    point_id = generate_uuid(doc["chunk_id"])
    
    # DB에 넣을 데이터 구조체 생성 (메타데이터 포함)
    point = PointStruct(
        id=point_id,
        vector=vector,
        payload={
            "chunk_id": doc["chunk_id"], # 원래 ID도 메타데이터로 보관
            "topic": doc["topic"],
            "source": doc["source"],
            "source_file": doc["source_file"], # 파일 출처
            "tags": doc["tags"],
            "content": doc["content"] # 실제 RAG에서 활용할 원문
        }
    )
    points.append(point)

# Qdrant에 일괄 저장 (Upsert)
if points:
    client.upsert(
        collection_name=collection_name,
        points=points
    )
    print(f"\n✨ 데이터 적재 완료! 총 {len(points)}개의 청크가 '{DB_DIR}' 경로에 성공적으로 저장되었습니다.")
else:
    print("\n저장할 데이터가 없습니다. data 폴더 내의 파일들을 다시 확인해주세요.")
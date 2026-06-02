"""
Data Ingestion Pipeline for RAG (Retrieval-Augmented Generation) System

이 스크립트는 원본 JSON 형태의 정책/세무 데이터를 읽어와 
SentenceTransformer(BGE-M3) 모델을 이용해 임베딩(Embedding)을 수행한 후, 
로컬 환경의 Qdrant Vector Database에 적재(Upsert)하는 파이프라인 역할을 합니다.

Note:
    - 현재 로컬 파일 시스템 기반의 Qdrant를 사용 중입니다 (`qdrant_db_local` 디렉토리).
    - 향후 운영(Production) 환경 배포 시 QdrantClient 연결 설정을 url, api_key 형태로 변경해야 합니다.
"""

import json
import uuid
import hashlib
import os
from typing import List, Dict, Any

from qdrant_client import QdrantClient
from qdrant_client.models import VectorParams, Distance, PointStruct
from sentence_transformers import SentenceTransformer

# =====================================================================
# 1. Global Configurations & Paths (전역 설정)
# =====================================================================
# 프로젝트 최상위 및 데이터/DB 디렉토리 경로 동적 할당
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, 'data')
DB_DIR = os.path.join(BASE_DIR, 'qdrant_db_local')

COLLECTION_NAME = "tax_youth_policy"
EMBEDDING_MODEL_NAME = 'BAAI/bge-m3'

# 처리 대상 JSON 파일 목록 정의
TARGET_JSON_FILES = [
    'yearend_tax_rag_data_v3.json',
    'yearend_tax_rag_supplementary.json',
    'youth_housing_welfare_rag_v2.json',
    'youth_asset_job_policy_rag_2026_v3.json',
    'youth_rent_support_rag_2026_v2.json'
]


def generate_deterministic_uuid(string_id: str) -> str:
    """
    고유 문자열 ID(chunk_id)를 기반으로 일관된(Deterministic) UUID를 생성합니다.
    
    Qdrant는 Point ID로 UUID 포맷을 요구합니다. 
    동일한 데이터가 중복 적재되는 것을 방지하기 위해 MD5 해시를 사용하여 
    항상 동일한 문자열("H001" 등)에 대해 동일한 UUID를 반환하도록 설계했습니다.

    Args:
        string_id (str): 원본 문서의 고유 식별자

    Returns:
        str: UUID 형식의 문자열
    """
    hash_obj = hashlib.md5(string_id.encode('utf-8'))
    return str(uuid.UUID(hash_obj.hexdigest()))


def load_documents(data_dir: str, file_list: List[str]) -> List[Dict[str, Any]]:
    """
    지정된 디렉토리에서 여러 JSON 파일을 읽어와 하나의 리스트로 병합합니다.
    
    Args:
        data_dir (str): JSON 파일들이 위치한 디렉토리 경로
        file_list (List[str]): 읽어올 JSON 파일명 목록

    Returns:
        List[Dict[str, Any]]: 모든 파일에서 추출한 청크(Document) 리스트
    """
    all_docs = []
    
    for filename in file_list:
        file_path = os.path.join(data_dir, filename)
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                docs = json.load(f)
                
                # 메타데이터 강화: 출처 역추적을 위해 원본 파일명을 payload에 주입
                for doc in docs:
                    doc['source_file'] = filename 
                
                all_docs.extend(docs)
                # TODO: 실제 운영 환경에서는 Python logging 모듈(logger.info) 사용 권장
                print(f"[INFO] '{filename}' 파일에서 {len(docs)}개의 청크 로드 완료.")
                
        except FileNotFoundError:
            print(f"[WARNING] 파일을 찾을 수 없습니다. 경로 건너뜀: {file_path}")
        except json.JSONDecodeError:
            print(f"[ERROR] JSON 파싱 실패. 파일 포맷 확인 필요: {file_path}")
            
    return all_docs


def main():
    """
    데이터 인제스천(Ingestion) 메인 파이프라인
    """
    # =====================================================================
    # 2. Qdrant Client Initialization & Collection Setup
    # =====================================================================
    # 로컬 디렉토리 기반 DB 연결 (Persistent 모드)
    client = QdrantClient(path=DB_DIR)
    
    print(f"\n[INFO] 임베딩 모델 '{EMBEDDING_MODEL_NAME}' 로딩 중...")
    model = SentenceTransformer(EMBEDDING_MODEL_NAME)
    vector_size = model.get_sentence_embedding_dimension() # BGE-M3: 1024차원 반환

    # Collection 존재 여부 확인 및 신규 생성
    if not client.collection_exists(COLLECTION_NAME):
        print(f"[INFO] '{COLLECTION_NAME}' 컬렉션이 없어 새로 생성합니다.")
        client.create_collection(
            collection_name=COLLECTION_NAME,
            # Cosine Similarity(코사인 유사도)를 기준으로 벡터 간 거리 측정
            vectors_config=VectorParams(size=vector_size, distance=Distance.COSINE),
        )
    else:
        print(f"[INFO] '{COLLECTION_NAME}' 컬렉션이 이미 존재합니다. (기존 데이터 덮어쓰기/업데이트 진행)")

    # =====================================================================
    # 3. Data Loading
    # =====================================================================
    all_docs = load_documents(DATA_DIR, TARGET_JSON_FILES)
    
    if not all_docs:
        print("[WARNING] 적재할 문서가 없습니다. 프로세스를 종료합니다.")
        return

    # =====================================================================
    # 4. Vector Embedding & Qdrant Upsert
    # =====================================================================
    print(f"\n[INFO] 총 {len(all_docs)}개 청크 임베딩 추출 및 DB 적재 시작 (시간이 다소 소요될 수 있습니다)...")
    
    points = []
    for doc in all_docs:
        # 본문(content) 텍스트를 고차원 벡터로 인코딩
        vector = model.encode(doc.get("content", "")).tolist()
        
        # Qdrant 식별자(UUID) 생성
        point_id = generate_deterministic_uuid(doc["chunk_id"])
        
        # 검색 시 LLM 및 프론트엔드로 전달될 Payload(메타데이터) 구성
        # 런타임 에러 방지를 위해 .get() 메서드 활용
        payload = {
            "chunk_id": doc.get("chunk_id", ""),        
            "topic": doc.get("topic", ""),              
            "source": doc.get("source", ""),
            "source_file": doc.get("source_file", ""),  
            "tags": doc.get("tags", []),
            "content": doc.get("content", "")           
        }
        
        # Qdrant Point 객체 생성
        point = PointStruct(id=point_id, vector=vector, payload=payload)
        points.append(point)

    # 생성된 Point 리스트를 Qdrant에 일괄 저장(Batch Upsert)
    # Note: 동일한 UUID(point_id)가 들어오면 기존 데이터를 덮어씁니다(Update).
    if points:
        client.upsert(
            collection_name=COLLECTION_NAME,
            points=points
        )
        print(f"\n[SUCCESS] ✨ 데이터 적재 완료! 총 {len(points)}개의 벡터가 '{DB_DIR}' 경로에 안전하게 저장되었습니다.")


if __name__ == "__main__":
    main()
    
import streamlit as st
import streamlit.components.v1 as components
import requests
import time
import json

# 1. 페이지 기본 설정 (가장 위에 와야 함)
st.set_page_config(
    page_title="청년 세무/정책 가이드",
    page_icon="🦙",
    layout="centered",
    initial_sidebar_state="expanded"
)

# FastAPI 백엔드 주소
API_URL = "http://127.0.0.1:8000/api/v1/chat"

# 2. 사이드바 구성 (사용 가이드 및 초기화 버튼)
with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/3063/3063822.png", width=100) 
    st.title("세금 가이드")
    st.markdown("어려운 세금과 청년 정책,<br>이제 일상어로 편하게 물어보세요!", unsafe_allow_html=True)
    
    st.divider()
    st.markdown("### 💡 이렇게 물어보세요")
    st.markdown("- **연말정산:** 월세 지원금 받으려면 전입신고 꼭 해야해?\n- **청년정책:** 버팀목 전세대출 조건 알려줘")
    st.divider()
    
    # 대화 초기화 버튼
    if st.button("🔄 대화 내용 초기화", use_container_width=True):
        st.session_state.messages = []
        st.rerun()

# 3. 메인 화면 헤더
st.title("내 손안의 세무/정책 가이드")
st.caption("국세청 데이터와 최신 청년 정책을 바탕으로 GPT-4o가 똑똑하게 답변합니다.")

# 4. 세션 상태(Session State) 초기화 (대화 기록 기억하기)
if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "assistant", "content": "안녕하세요! 청년들을 위한 세무/정책 가이드입니다. 연말정산이나 청년 지원 정책 중 궁금한 점을 편하게 말씀해 주세요! 😊"}
    ]

# 5. 기존 대화 내용 화면에 출력
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# 6. 사용자 입력창 및 전송 로직
if prompt := st.chat_input("질문을 입력해주세요... (예: 월세 세액공제 조건 알려줘)"):
    # 사용자 메시지 화면에 추가
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # AI 답변 대기 화면 및 API 호출
    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        
        # 스피너(로딩 애니메이션) 띄우기
        with st.spinner("문서를 뒤적이는 중... 🦙"):
            try:
                # 백엔드 API로 질문 전송
                response = requests.post(API_URL, json={"query": prompt})
                
                if response.status_code == 200:
                    data = response.json()
                    answer = data.get("answer", "답변을 생성하지 못했습니다.")
                    sources = data.get("sources", []) # 출처 리스트 받아오기
                    
                    # 1. 텍스트가 타자 치듯 나오는 애니메이션 효과
                    full_response = ""
                    for chunk in answer.split(" "):
                        full_response += chunk + " "
                        time.sleep(0.05)
                        message_placeholder.markdown(full_response + "▌")
                    
                    message_placeholder.markdown(full_response)
                    
                    # 2. 사전 형태로 출처 보여주기 (접고 펼치기 기능)
                    if sources:
                        with st.expander("📚 참조한 원본 사전 데이터 보기"):
                            for idx, src in enumerate(sources, 1):
                                # 표제어 (사전의 단어 느낌)
                                st.markdown(f"### 📖 {src.get('주제', '주제 없음')}")
                                
                                # 출처 (작은 글씨로 파일명 표시)
                                st.caption(f"📂 출처 문서: {src.get('출처파일명', '알 수 없음')}")
                                
                                # 뜻풀이 (사전의 설명 부분처럼 깔끔한 인용구 박스 처리)
                                st.info(f"{src.get('원문내용', '내용이 없습니다.')}")
                                
                                # 단어 사이를 나누는 얇은 선
                                if idx < len(sources):
                                    st.divider()
                    
                    # 세션에 AI 답변 저장
                    st.session_state.messages.append({"role": "assistant", "content": full_response})
                    
                    # ---------------------------------------------------------
                    # 3. [추가된 부분] 답변 출력이 완료된 후 프론트엔드(브라우저) TTS 실행
                    # 파이썬 문자열을 JS 환경에 안전하게 넘기기 위해 json.dumps 사용
                    safe_answer = json.dumps(answer)
                    
                    tts_js = f"""
                    <script>
                        function speakText() {{
                            if (!window.speechSynthesis) return;
                            
                            // 겹침 방지를 위해 진행 중인 음성 취소
                            window.speechSynthesis.cancel();
                            
                            // 파이썬에서 넘겨준 안전한 문자열 변수
                            const rawText = {safe_answer};
                            
                            // 마크다운 기호(*, #, _) 및 [출처: ~] 텍스트 제거
                            let cleanedText = rawText.replace(/[*#_~`>]/g, "").replace(/\\[출처:.*?\\]/g, "");
                            
                            const utterance = new SpeechSynthesisUtterance(cleanedText);
                            utterance.lang = "ko-KR";
                            utterance.rate = 1.0;
                            utterance.pitch = 1.0;
                            
                            window.speechSynthesis.speak(utterance);
                        }}
                        
                        // 즉시 실행
                        speakText();
                    </script>
                    """
                    # 화면에 보이지 않는 HTML 컴포넌트로 스크립트 실행 (높이 0)
                    components.html(tts_js, height=0)
                    # ---------------------------------------------------------

                else:
                    st.error(f"서버 오류가 발생했습니다. (상태 코드: {response.status_code})")
            except requests.exceptions.ConnectionError:
                st.error("🚨 백엔드 서버(FastAPI)가 꺼져있는 것 같습니다. 터미널에서 백엔드 서버를 먼저 켜주세요!")
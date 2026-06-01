import "./Sidebar.css";

const exampleQuestions = [
  { id: 'ex1', category: '연말 정산', text: '월세 지원금 받으려면 전입신고 꼭 해야해?' },
  { id: 'ex2', category: '청년 정책', text: '버팀목 전세 대출 조건 알려줘' },
  { id: 'ex3', category: '세무 용어', text: '원천징수가 뭐야?' },
];

/**
 * Sidebar 컴포넌트
 * 좌측 메뉴바를 렌더링하며, 대화 목록 관리 및 예시 질문을 제공합니다.
 * 
 * @param {Object} props
 * @param {Function} props.onNewChat - '새 대화 시작' 버튼 클릭 시 실행될 함수
 * @param {number} props.currentChatId - 현재 활성화된(보고 있는) 대화방의 고유 ID
 * @param {Function} props.onSelectChat - 사이드바에서 특정 대화방 클릭 시 실행될 함수
 * @param {Function} props.onGoHome - '처음으로' 버튼 클릭 시 메인 랜딩 페이지로 돌아가는 함수
 * @param {Array} props.chats - 최근 대화방 목록 데이터 배열
 * @param {Function} props.onExampleClick - 예시 질문 클릭 시 대화방에 메시지를 자동 전송하는 함수
 * @param {Function} props.onClearChats - 대화방 목록을 모두 지우고 초기화하는 함수
 */
const Sidebar = ({ onNewChat, currentChatId, onSelectChat, onGoHome, chats, onExampleClick, onClearChats }) => {
  return (
    <aside className="sidebar">
      <div className="sidebar-header">
        <div className="sidebar-logo">
          <div className="sidebar-logo-icon">청</div>
          <span className="sidebar-logo-text">청년정책봇</span>
        </div>
      </div>

      <button className="new-chat-btn" onClick={onNewChat}>
        <span className="new-chat-icon">+</span>
        <span className="new-chat-text">새 대화 시작</span>
      </button>

      <div className="sidebar-section-label">질문 예시</div>
      <ul className="chat-list">
        {exampleQuestions.map((q) => (
          <li
            key={q.id}
            className="chat-item example-item"
            onClick={() => onExampleClick(q.text)}
          >
            <span className="chat-icon">💡</span>
            <span className="chat-title">[{q.category}] {q.text}</span>
          </li>
        ))}
      </ul>

      <div className="sidebar-section-label">최근 대화</div>

      <ul className="chat-list">
        {chats.map((chat) => (
          <li
            key={chat.id}
            className={`chat-item ${currentChatId === chat.id ? "active" : ""}`}
            onClick={() => onSelectChat(chat.id)}
          >
            <span className="chat-icon">☰</span>
            <span className="chat-title">{chat.title}</span>
          </li>
        ))}
      </ul>

      <div className="sidebar-footer">
        <button className="back-home-btn" onClick={onClearChats}>
          <span className="back-home-icon">🗑</span>
          <span className="back-home-text">대화 초기화</span>
        </button>
        <button className="back-home-btn" onClick={onGoHome}>
          <span className="back-home-icon">←</span>
          <span className="back-home-text">처음으로</span>
        </button>
      </div>
    </aside>
  );
};

export default Sidebar;

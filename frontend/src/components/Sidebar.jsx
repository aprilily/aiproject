import "./Sidebar.css";

const exampleQuestions = [
  { id: 'ex1', category: '연말 정산', text: '월세 지원금 받으려면 전입신고 꼭 해야해?' },
  { id: 'ex2', category: '청년 정책', text: '버팀목 전세 대출 조건 알려줘' },
  { id: 'ex3', category: '세무 용어', text: '원천징수가 뭐야?' },
];

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

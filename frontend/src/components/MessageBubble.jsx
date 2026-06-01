import SourceChip from "./SourceChip";

import "./MessageBubble.css";



/**
 * MessageBubble 컴포넌트
 * 채팅창 내에서 사용자 또는 봇의 메시지 1개를 렌더링합니다.
 * 봇 메시지의 경우 출처 링크와 추천 키워드 칩을 함께 표시할 수 있습니다.
 * 
 * @param {Object} props
 * @param {string} props.role - 메시지 작성자 ('user' 또는 'bot')
 * @param {string} props.content - 메시지 본문 내용 (HTML 렌더링 지원)
 * @param {Array} props.sources - 봇 메시지의 출처 목록 데이터
 * @param {Array} props.suggestions - 봇 메시지 하단에 표시될 추천 검색어(키워드) 목록
 * @param {Function} props.onSuggestionClick - 추천 키워드 클릭 시 실행될 콜백 핸들러
 */
const MessageBubble = ({ role, content, sources, suggestions, onSuggestionClick }) => {

  const isUser = role === "user";

  return (
    <div className={`bubble-wrapper ${isUser ? "bubble-user" : "bubble-bot"}`}>
      {!isUser && (
        <div className="bot-avatar">봇</div>
        )}

      <div className={`bubble ${isUser ? "bubble-user-box" : "bubble-bot-box"}`}>
        <div
        className="bubble-content"
        dangerouslySetInnerHTML={{ __html: content.replace(/\n/g, "<br/>") }}
        />

        {sources && sources.length > 0 && (
        <div className="bubble-sources">
          {sources.map((src, i) => (
          <SourceChip key={i} label={src.label} href={src.href} />
          ))}
        </div>
        )}

        {suggestions && suggestions.length > 0 && (
        <div className="bubble-suggestions">
          {suggestions.map((suggestion, i) => (
          <button
            key={i}
            className="suggestion-chip"
            onClick={() => onSuggestionClick && onSuggestionClick(suggestion)}
          >
            {suggestion}
          </button>
          ))}
        </div>
        )}
        </div>
      {isUser && (
      <div className="user-avatar">나</div>
      )}
    </div>
  );
};



export default MessageBubble;
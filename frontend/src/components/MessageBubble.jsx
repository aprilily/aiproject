import SourceChip from "./SourceChip";
import "./MessageBubble.css";

const MessageBubble = ({ role, content, sources }) => {
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
      </div>
      {isUser && (
        <div className="user-avatar">나</div>
      )}
    </div>
  );
};

export default MessageBubble;

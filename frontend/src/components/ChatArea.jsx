import { useEffect, useRef, useState } from "react";
import MessageBubble from "./MessageBubble";
import "./ChatArea.css";

/**
 * ChatArea 컴포넌트
 * 채팅 메시지 목록이 표시되는 메인 영역입니다.
 * 자동 스크롤 제어 및 우측 상단의 공유 메뉴 기능을 관리합니다.
 * 
 * @param {Object} props
 * @param {Array} props.messages - 렌더링할 채팅 메시지 객체 배열
 * @param {string} props.title - 상단 헤더에 표시될 현재 대화방의 제목
 * @param {Function} props.onSuggestionClick - 메시지 내 추천 키워드(칩) 클릭 시 실행될 콜백 함수
 */
const ChatArea = ({ messages, title, onSuggestionClick }) => {
  const bottomRef = useRef(null);
  const [showShareMenu, setShowShareMenu] = useState(false);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const toggleShareMenu = () => {
    setShowShareMenu((prev) => !prev);
  };

  const handleShare = async (platform) => {
    setShowShareMenu(false);
    const shareText = `[청년정책봇] ${title}\n\n도움이 되는 정책 정보를 확인해보세요!`;
    const shareUrl = window.location.href;

    if (platform === "native" && navigator.share) {
      try {
        await navigator.share({
          title: title,
          text: shareText,
          url: shareUrl,
        });
        return;
      } catch (error) {
        console.log("Error sharing natively:", error);
      }
    } else if (platform === "kakao") {
      alert("카카오톡 공유 API(Kakao.Link.sendDefault 등) 연동이 필요합니다.");
    } else if (platform === "sms") {
      window.location.href = `sms:?body=${encodeURIComponent(shareText + "\n" + shareUrl)}`;
    } else if (platform === "copy") {
      navigator.clipboard.writeText(`${shareText}\n${shareUrl}`).then(() => {
        alert("링크가 클립보드에 복사되었습니다.");
      });
    }
  };

  useEffect(() => {
    const handleClickOutside = (event) => {
      if (showShareMenu && !event.target.closest('.share-menu-container')) {
        setShowShareMenu(false);
      }
    };
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, [showShareMenu]);

  return (
    <div className="chat-area">
      <div className="chat-header">
        <div className="chat-header-left">
          <span className="chat-header-icon">☰</span>
          <span className="chat-header-title">{title || "청년미래적금 가입 조건"}</span>
          <span className="chat-header-badge">2026 최신</span>
        </div>
        <div className="chat-header-right">
          <div className="share-menu-container" style={{ position: 'relative' }}>
            <button className="header-btn" onClick={toggleShareMenu}>🔗</button>
            {showShareMenu && (
              <div className="share-dropdown">
                <div className="share-dropdown-item" onClick={() => handleShare("native")}>
                  <span className="share-icon">📤</span> 다른 앱으로 공유
                </div>
                <div className="share-dropdown-item" onClick={() => handleShare("kakao")}>
                  <span className="share-icon" style={{color: '#FEE500'}}>💬</span> 카카오톡 공유
                </div>
                <div className="share-dropdown-item" onClick={() => handleShare("sms")}>
                  <span className="share-icon">✉️</span> 문자 메시지(SMS)
                </div>
                <div className="share-dropdown-item" onClick={() => handleShare("copy")}>
                  <span className="share-icon">📋</span> 링크 복사
                </div>
              </div>
            )}
          </div>
          <button className="header-btn">⋯</button>
        </div>
      </div>

      <div className="chat-messages">
        <div className="chat-messages-inner">
          {messages.map((msg, i) => (
            <MessageBubble
              key={i}
              role={msg.role}
              content={msg.content}
              sources={msg.sources}
              suggestions={msg.suggestions} // 👈 추가됨
              onSuggestionClick={onSuggestionClick} // 👈 추가됨
            />
          ))}
          <div ref={bottomRef} />
        </div>
      </div>
    </div>
  );
};

export default ChatArea;
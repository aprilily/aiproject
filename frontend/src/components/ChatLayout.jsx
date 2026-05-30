import { useState, useEffect, useRef } from "react";
import Sidebar from "./Sidebar";
import ChatArea from "./ChatArea";
import InputBar from "./InputBar";
import "./ChatLayout.css";

const SUGGESTIONS = ["🏦 금융 정책", "🏠 주거 지원", "📋 용어 검색"];

const MOCK_CHATS = {
  1: {
    title: "새 대화",
    messages: [
      {
        role: "bot",
        content: "무엇을 도와드릴까요? 아래 키워드를 선택하거나 청년 정책에 대해 질문해주세요.",
        sources: [],
        suggestions: SUGGESTIONS // 칩 데이터 주입
      }
    ],
  }
};

const ChatLayout = ({ onGoHome, initialMessage }) => {
  const [sessions, setSessions] = useState(MOCK_CHATS);
  const [currentChatId, setCurrentChatId] = useState(1);
  const [loading, setLoading] = useState(false);
  const hasSentInitialRef = useRef(false);

  const currentMessages = sessions[currentChatId]?.messages || [];
  const currentTitle = sessions[currentChatId]?.title || "새 대화";

  const handleNewChat = () => {
    const newId = Date.now();
    setSessions((prev) => ({
      ...prev,
      [newId]: {
        title: "새 대화",
        messages: [{
          role: "bot",
          content: "무엇을 도와드릴까요? 아래 키워드를 선택하거나 청년 정책에 대해 질문해주세요.",
          sources: [],
          suggestions: SUGGESTIONS // 칩 데이터 주입
        }]
      }
    }));
    setCurrentChatId(newId);
  };

  const handleSelectChat = (id) => {
    setCurrentChatId(id);
  };

  const handleClearChats = () => {
    const newId = Date.now();
    setSessions({
      [newId]: {
        title: "새 대화",
        messages: [{
          role: "bot",
          content: "무엇을 도와드릴까요? 아래 키워드를 선택하거나 청년 정책에 대해 질문해주세요.",
          sources: [],
          suggestions: SUGGESTIONS // 칩 데이터 주입
        }]
      }
    });
    setCurrentChatId(newId);
  }

  const chatsList = Object.entries(sessions)
    .map(([id, session]) => ({ id: Number(id), title: session.title }))
    .sort((a, b) => b.id - a.id);

  const handleSend = async (text, targetChatId = currentChatId) => {
    const userMsg = { role: "user", content: text };
    
    setSessions((prev) => {
      const session = prev[targetChatId] || { title: "새 대화", messages: [] };
      return {
        ...prev,
        [targetChatId]: {
          ...session,
          title: session.title === "새 대화" ? text.slice(0, 15) : session.title,
          messages: [...session.messages, userMsg],
        }
      };
    });

    setLoading(true);

    setSessions((prev) => {
      const session = prev[targetChatId] || { title: "새 대화", messages: [] };
      return {
        ...prev,
        [targetChatId]: {
          ...session,
          messages: [
            ...session.messages,
            {
              role: "bot",
              content: "관련 정책 정보를 찾고 있어요. 잠시만 기다려 주세요...",
              sources: [],
              isTemporary: true
            },
          ]
        }
      };
    });

    try {
      const response = await fetch("http://127.0.0.1:8000/api/v1/chat", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ query: text }),
      });

      const data = await response.json();

      let botContent = "";
      let botSources = [];

      if (data.status === "success") {
        botContent = data.answer;
        if (data.sources && Array.isArray(data.sources)) {
          const allLinks = [];
          data.sources.forEach((source) => {
            if (source.links && Array.isArray(source.links) && source.links.length > 0) {
              source.links.forEach((link) => {
                allLinks.push({
                  label: link.title || source.출처파일명 || source.주제 || "출처",
                  href: link.url || "#",
                });
              });
            } else {
              allLinks.push({
                label: source.출처파일명 || source.주제 || "출처",
                href: "#",
              });
            }
          });

          // URL(또는 라벨)을 기준으로 중복 제거
          const uniqueMap = new Map();
          allLinks.forEach((item) => {
            const key = item.href !== "#" ? item.href : item.label;
            if (!uniqueMap.has(key)) {
              uniqueMap.set(key, item);
            }
          });
          botSources = Array.from(uniqueMap.values());
        }
      } else {
        botContent = data.message || "오류가 발생했습니다.";
      }

      setSessions((prev) => {
        const session = prev[targetChatId] || { title: "새 대화", messages: [] };
        const filteredMsgs = session.messages.filter(msg => !msg.isTemporary);
        
        return {
          ...prev,
          [targetChatId]: {
            ...session,
            messages: [
              ...filteredMsgs,
              {
                role: "bot",
                content: botContent,
                sources: botSources,
              }
            ]
          }
        };
      });
    } catch (error) {
      console.error("API Error:", error);
      setSessions((prev) => {
        const session = prev[targetChatId] || { title: "새 대화", messages: [] };
        const filteredMsgs = session.messages.filter(msg => !msg.isTemporary);
        
        return {
          ...prev,
          [targetChatId]: {
            ...session,
            messages: [
              ...filteredMsgs,
              {
                role: "bot",
                content: "서버와 통신하는 중 오류가 발생했습니다. 잠시 후 다시 시도해주세요.",
                sources: [],
              }
            ]
          }
        };
      });
    } finally {
      setLoading(false);
    }
  };

  // 초기 메시지가 있을 때 첫 대화 생성 후 자동으로 전송
  useEffect(() => {
    if (initialMessage && !hasSentInitialRef.current) {
      hasSentInitialRef.current = true; // 메시지를 보냈다고 기록
      setTimeout(() => {
        // 새로 방을 만들지 않고 현재 있는 빈 '새 대화' 방을 그대로 사용
        handleSend(initialMessage, currentChatId);
      }, 0);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [initialMessage]);

  return (
    <div className="chat-layout">
      <Sidebar
        onNewChat={handleNewChat}
        currentChatId={currentChatId}
        onSelectChat={handleSelectChat}
        onGoHome={onGoHome}
        chats={chatsList}
        onExampleClick={handleSend}
        onClearChats={handleClearChats}
      />
      <div className="chat-main">
        {/* onSuggestionClick 프롭 추가 */}
        <ChatArea 
          messages={currentMessages} 
          title={currentTitle} 
          onSuggestionClick={(suggestion) => {
            const cleanText = suggestion.replace(/^[^a-zA-Z가-힣0-9]+\s*/, "");
            handleSend(`${cleanText}이 궁금해요`);
          }} 
        />
        <InputBar onSend={handleSend} disabled={loading} />
      </div>
    </div>
  );
};

export default ChatLayout;
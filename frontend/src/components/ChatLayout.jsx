import { useState } from "react";
import Sidebar from "./Sidebar";
import ChatArea from "./ChatArea";
import InputBar from "./InputBar";
import "./ChatLayout.css";

const MOCK_CHATS = {
  1: {
    title: "청년미래적금 가입 조건",
    messages: [
      {
        role: "bot",
        content: "· 이자소득 비과세, 최대 금리 7~8%",
        sources: [
          { label: "노소뱅크 청년미래적금", href: "https://www.fsc.go.kr" },
          { label: "금융위원회 2026.5", href: "https://www.fsc.go.kr" },
        ],
      },
      {
        role: "user",
        content: "우대형 조건은 뭐야?",
      },
      {
        role: "bot",
        content:
          "우대형은 일반형보다 정부 기여금이 2배에요.\n\n우대형 조건 (둘 중 하나 해당 시)\n· 개인소득 3,600만원 이하 + 가구 중위소득 150% 이하\n· 중소기업 신규취업자 (입사 6개월 이내)\n\n우대형 혜택\n· 정부 기여금 12% (일반형의 2배)\n· 월 50만원 × 3년 납입 시 약 2,200~2,255만원 수령 예상",
        sources: [{ label: "청년도약계좌", href: "https://ylaccount.kinfa.or.kr/" }],
      },
    ],
  },
  2: {
    title: "버팀목 전세자금 금리",
    messages: [
      {
        role: "user",
        content: "버팀목 전세자금대출 금리가 어떻게 돼?",
      },
      {
        role: "bot",
        content: "청년 전용 버팀목 전세자금대출 금리는 소득에 따라 연 1.5% ~ 2.1% 가 적용됩니다.\n\n우대금리 조건:\n· 연소득 4천만원 이하, 기초생활수급권자, 차상위계층, 한부모가족 (연 1.0%p)\n· 청년 우대 (연 0.3%p)",
        sources: [{ label: "주택도시기금 2026", href: "https://nhuf.molit.go.kr/" }],
      }
    ],
  },
  3: {
    title: "서울시 월세지원 신청",
    messages: [
      {
        role: "user",
        content: "서울시 청년 월세지원 어떻게 신청해?",
      },
      {
        role: "bot",
        content: "서울시 청년월세지원은 '서울주거포털'에서 온라인 신청이 가능합니다.\n\n지원 대상:\n· 신청일 기준 서울시에 거주하는 만 19세~39세 청년 1인 가구\n· 기준중위소득 150% 이하\n\n지원 내용:\n· 월 20만원씩 최대 12개월(240만원) 지원",
        sources: [{ label: "서울주거포털", href: "https://housing.seoul.go.kr/" }],
      }
    ],
  },
  4: {
    title: "연말정산 자녀공제",
    messages: [
      {
        role: "user",
        content: "연말정산 자녀세액공제에 대해 알려줘",
      },
      {
        role: "bot",
        content: "자녀세액공제는 만 8세 이상의 기본공제대상 자녀에 대해 세액을 공제해주는 제도입니다.\n\n공제액:\n· 자녀 1명: 15만원\n· 자녀 2명: 30만원\n· 자녀 3명 이상: 30만원 + 2명 초과 1명당 30만원",
        sources: [{ label: "국세청 홈택스", href: "https://www.hometax.go.kr/" }],
      }
    ],
  }
};

const ChatLayout = ({ onGoHome }) => {
  const [sessions, setSessions] = useState(MOCK_CHATS);
  const [currentChatId, setCurrentChatId] = useState(1);
  const [loading, setLoading] = useState(false);

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
          content: "무엇을 도와드릴까요? 청년 정책에 대해 질문해주세요.",
          sources: []
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
          content: "무엇을 도와드릴까요? 청년 정책에 대해 질문해주세요.",
          sources: []
        }]
      }
    });
    setCurrentChatId(newId);
  }

  const chatsList = Object.entries(sessions)
    .map(([id, session]) => ({ id: Number(id), title: session.title }))
    .sort((a, b) => b.id - a.id); // Show newest first if id is timestamp, but our mock ids are 1, 2, 3, 4. Actually let's just sort descending.

  const handleSend = async (text) => {
    const userMsg = { role: "user", content: text };
    
    setSessions((prev) => ({
      ...prev,
      [currentChatId]: {
        ...prev[currentChatId],
        title: prev[currentChatId].title === "새 대화" ? text.slice(0, 15) : prev[currentChatId].title,
        messages: [...prev[currentChatId].messages, userMsg],
      }
    }));

    setLoading(true);

    setSessions((prev) => ({
      ...prev,
      [currentChatId]: {
        ...prev[currentChatId],
        messages: [
          ...prev[currentChatId].messages,
          {
            role: "bot",
            content: "관련 정책 정보를 찾고 있어요. 잠시만 기다려 주세요...",
            sources: [],
            isTemporary: true
          },
        ]
      }
    }));

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
          botSources = data.sources.map((source) => ({
            label: source.출처파일명 || "출처",
            href: "#",
          }));
        }
      } else {
        botContent = data.message || "오류가 발생했습니다.";
      }

      setSessions((prev) => {
        const currentMsgs = prev[currentChatId].messages;
        const filteredMsgs = currentMsgs.filter(msg => !msg.isTemporary);
        
        return {
          ...prev,
          [currentChatId]: {
            ...prev[currentChatId],
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
        const currentMsgs = prev[currentChatId].messages;
        const filteredMsgs = currentMsgs.filter(msg => !msg.isTemporary);
        
        return {
          ...prev,
          [currentChatId]: {
            ...prev[currentChatId],
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
        <ChatArea messages={currentMessages} title={currentTitle} />
        <InputBar onSend={handleSend} disabled={loading} />
      </div>
    </div>
  );
};

export default ChatLayout;

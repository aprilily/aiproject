import { useState, useRef, useEffect } from "react";
import "./InputBar.css";

/**
 * InputBar 컴포넌트
 * 사용자가 메시지를 입력하고 전송하는 하단 고정 영역입니다.
 * Shift + Enter를 통한 줄바꿈 및 한글 IME(조합 중) 입력 시 조기 전송 방지 로직이 포함되어 있습니다.
 * 
 * @param {Object} props
 * @param {Function} props.onSend - 메시지 전송 버튼 클릭 또는 Enter 키 입력 시 실행되는 핸들러 (입력된 텍스트 전달)
 * @param {boolean} props.disabled - 로딩 중이거나 전송이 불가능한 상태일 때 텍스트 입력창 및 버튼 비활성화 처리 여부
 */
const InputBar = ({ onSend, disabled }) => {
  const [value, setValue] = useState("");
  const textareaRef = useRef(null);

  const adjustHeight = () => {
    if (textareaRef.current) {
      textareaRef.current.style.height = "auto";
      textareaRef.current.style.height = `${Math.min(textareaRef.current.scrollHeight, 120)}px`;
    }
  };

  useEffect(() => {
    adjustHeight();
  }, [value]);

  const handleSend = () => {
    if (value.trim() && !disabled) {
      onSend(value.trim());
      setValue("");
      if (textareaRef.current) {
        textareaRef.current.style.height = "auto";
      }
    }
  };

  const handleKeyDown = (e) => {
    // If Shift + Enter is pressed, allow normal new line
    // If only Enter is pressed, send message
    if (e.key === "Enter" && !e.shiftKey) {
      // Allow composing mode for CJK characters (IME) to prevent premature sending
      if (e.nativeEvent.isComposing) return;
      
      e.preventDefault();
      handleSend();
    }
  };

  return (
    <div className="input-bar-wrapper">
      <div className="input-bar-inner">
        <div className="input-bar">
          <textarea
            ref={textareaRef}
            className="input-textarea"
            placeholder="청년 금융·주거 정책에 대해 질문해 보세요..."
            value={value}
            onChange={(e) => setValue(e.target.value)}
            onKeyDown={handleKeyDown}
            rows={1}
            disabled={disabled}
          />
          <button
            className="send-btn"
            onClick={handleSend}
            disabled={!value.trim() || disabled}
          >
            ↑
          </button>
        </div>
        <p className="input-footer">
          정부 공식 자료 기반 답변 · 출처 버튼을 누르면 원본 페이지로 이동해요
        </p>
      </div>
    </div>
  );
};

export default InputBar;

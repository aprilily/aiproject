import { useState, useRef, useEffect } from "react";
import "./InputBar.css";

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

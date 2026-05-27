import "./LandingPage.css";

const LandingPage = ({ onStart }) => {
  const handleTagClick = (tagText) => {
    onStart(tagText);
  };

  return (
    <div className="landing-container">
      <div className="landing-content">
        <span className="badge">2026년 최신 정책 반영</span>

        <div className="landing-icon">
          <svg width="36" height="36" viewBox="0 0 24 24" fill="none">
            <path
              d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-1 14H9V8h2v8zm4 0h-2V8h2v8z"
              fill="white"
              opacity="0.3"
            />
            <rect x="8" y="10" width="2" height="5" rx="1" fill="white" />
            <rect x="14" y="8" width="2" height="7" rx="1" fill="white" />
            <circle cx="9" cy="8.5" r="1.5" fill="white" />
            <circle cx="15" cy="6.5" r="1.5" fill="white" />
            <path d="M9 9.5 L15 7.5" stroke="white" strokeWidth="1.5" strokeLinecap="round" />
          </svg>
        </div>

        <h1 className="landing-title">
          청년 정책 검색부터<br />용어 설명까지 한 번에
        </h1>

        <p className="landing-desc">
          금융 . 주거 정책 지원 정보와 어려운 세무 용어를<br />
          쉽고 빠르게 찾아드려요.
        </p>

        <button className="start-btn" onClick={() => onStart()}>
          <span>→</span> 시작하기
        </button>

        <div className="tag-row">
          <span className="tag" onClick={() => handleTagClick("🏦 금융 정책")}>🏦 금융 정책</span>
          <span className="tag" onClick={() => handleTagClick("🏠 주거 지원")}>🏠 주거 지원</span>
          <span className="tag" onClick={() => handleTagClick("📋 용어 검색")}>📋 용어 검색</span>
          <span className="tag" onClick={() => handleTagClick("📄 출처 확인")}>📄 출처 확인</span>
        </div>

        <p className="footer-note">정부 공식 자료 기반 · 로그인 없이 이용 가능</p>
      </div>
    </div>
  );
};

export default LandingPage;

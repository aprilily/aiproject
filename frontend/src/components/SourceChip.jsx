import "./SourceChip.css";

/**
 * SourceChip 컴포넌트
 * AI 답변 하단에 표시되는 출처 링크 버튼(칩)입니다.
 * 클릭 시 새 창에서 원본 URL로 이동합니다.
 * 
 * @param {Object} props
 * @param {string} props.label - 버튼에 표시될 텍스트 (예: '국세청 블로그')
 * @param {string} props.href - 클릭 시 이동할 원본 URL 링크
 */
const SourceChip = ({ label, href }) => {
  return (
    <a
      className="source-chip"
      href={href || "#"}
      target="_blank"
      rel="noopener noreferrer"
    >
      <span className="source-chip-icon">🔗</span>
      {label}
    </a>
  );
};

export default SourceChip;

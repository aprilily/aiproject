import "./SourceChip.css";

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

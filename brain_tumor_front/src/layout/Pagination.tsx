interface PaginationProps {
  currentPage: number;
  totalPages: number;
  onChange: (currentPage: number) => void;
  pageSize?: number; // 한 그룹에 보여줄 페이지 수 (기본 5)
}

export default function Pagination({
  currentPage,
  totalPages,
  onChange,
  pageSize = 5,
}: PaginationProps) {
  if (totalPages <= 1) return null;
  const currentGroup = Math.floor((currentPage - 1) / pageSize);
  const startPage = currentGroup * pageSize + 1;
  const endPage = Math.min(startPage + pageSize - 1, totalPages);
  // const pages = Array.from({ length: totalPages }, (_, i) => i + 1);
  // 그룹 범위만큼만 페이지 배열 생성
  const pages = endPage >= startPage
    ? Array.from({ length: endPage - startPage + 1 }, (_, i) => startPage + i)
    : [];



  return (
    <div className="pagination-bar">
      {currentGroup > 0 && (
        <button onClick={() => onChange(startPage - pageSize)}>{'<<'}</button>
      )}


      {/* 이전 */}
      <button
        className="page-btn"
        disabled={currentPage === 1}
        onClick={() => onChange(currentPage - 1)}
      >
        ◀
      </button>

      {/* 페이지 번호 */}
      {pages.map(p => (
        <button
          key={p}
          className={`page-btn ${p === currentPage ? 'active' : ''}`}
          onClick={() => onChange(p)}
        >
          {p}
        </button>
      ))}
 
      {/* 다음 */}
      <button
        className="page-btn"
        disabled={currentPage === totalPages}
        onClick={() => onChange(currentPage + 1)}
      >
        ▶
      </button>

      {endPage < totalPages && (
        <button onClick={() => onChange(startPage + pageSize)}>{'>>'}</button>
      )}
    </div>
  );
}

import { useLocation, useNavigate } from 'react-router-dom';

export default function PatientDetailHeader() {
  const navigate = useNavigate();
  const location = useLocation();

  const handleBack = () => {
    if (location.state?.from) {
      navigate(location.state.from);
    } else {
      navigate('/patients');
    }
  };

  return (
    <div className="page-header">
       <button onClick={handleBack} className="back-btn">
        ← 환자 목록으로
      </button>
      <div className="header-left">
        <h1>환자 상세</h1>
      </div>

      <div className="header-right">
        <button className="btn">환자 요약</button>
      </div>
    </div>
  );
}

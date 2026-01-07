import '@/assets/style/patientListView.css';

type Props = {
  role: string;
};

export default function SummaryTab({ role }: Props) {
  const isDoctor = role === 'DOCTOR';
  const isSystemManager = role === 'SYSTEMMANAGER';

  return (
    <div className="summary-layout">
      {/* 좌측 영역 */}
      <div className="summary-left">
        <div className="card">
          <h3>진료 요약</h3>
          <ul>
            <li>주진단: 뇌종양 의심</li>
            <li>주요 증상: 두통, 시야 장애</li>
            <li>최근 처방: MRI 촬영</li>
          </ul>
        </div>
      </div>

      {/* 우측 영역 */}
      <div className="summary-right">
        <div className="row">
          <div className="card small">
            <h4>영상 요약</h4>
            <p>최근 촬영: Brain MRI</p>
            <p>촬영일: 2025-03-10</p>
          </div>

          <div className="card small">
            <h4>검사 요약</h4>
            <p>혈액 검사</p>
            <p>이상 소견 없음</p>
          </div>
        </div>

        {(isDoctor || isSystemManager) && (
          <div className="card ai">
            <h4>AI 분석 요약</h4>
            <span className="badge badge-critical">Critical</span>
            <p>종양 의심 영역 1건</p>
            <p>위험도: Medium</p>
          </div>
        )}
      </div>
    </div>
  );
}

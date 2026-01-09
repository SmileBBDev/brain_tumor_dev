/**
 * OCS 결과 보고서 페이지
 * - CONFIRMED 상태의 OCS 결과를 보기 좋게 표시
 * - 환자 정보, 검사 정보, 결과 정보 포함
 * - 인쇄 기능 지원
 */
import { useState, useEffect, useCallback } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { getOCS } from '@/services/ocs.api';
import type { OCSDetail } from '@/types/ocs';
import './OCSResultReportPage.css';

// 날짜 포맷
const formatDate = (dateStr: string | null): string => {
  if (!dateStr) return '-';
  const date = new Date(dateStr);
  return date.toLocaleString('ko-KR', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
  });
};

// 날짜만 포맷
const formatDateOnly = (dateStr: string | null): string => {
  if (!dateStr) return '-';
  const date = new Date(dateStr);
  return date.toLocaleDateString('ko-KR', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
  });
};

export default function OCSResultReportPage() {
  const { ocsId } = useParams();
  const navigate = useNavigate();
  const [ocs, setOcs] = useState<OCSDetail | null>(null);
  const [loading, setLoading] = useState(true);

  const fetchOCSDetail = useCallback(async () => {
    if (!ocsId) return;

    setLoading(true);
    try {
      const data = await getOCS(parseInt(ocsId));
      setOcs(data);
    } catch (error) {
      console.error('Failed to fetch OCS detail:', error);
      alert('결과 정보를 불러오는데 실패했습니다.');
      navigate(-1);
    } finally {
      setLoading(false);
    }
  }, [ocsId, navigate]);

  useEffect(() => {
    fetchOCSDetail();
  }, [fetchOCSDetail]);

  // 인쇄
  const handlePrint = () => {
    window.print();
  };

  // 뒤로가기
  const handleBack = () => {
    navigate(-1);
  };

  if (loading) {
    return (
      <div className="ocs-result-report loading">
        <p>로딩 중...</p>
      </div>
    );
  }

  if (!ocs) {
    return (
      <div className="ocs-result-report error">
        <p>결과 정보를 찾을 수 없습니다.</p>
        <button className="btn btn-secondary" onClick={handleBack}>
          돌아가기
        </button>
      </div>
    );
  }

  // worker_result 파싱
  const workerResult = ocs.worker_result || {};

  // LIS 결과인 경우 labResults 추출
  const labResults = (workerResult as any).labResults || [];
  const interpretation = (workerResult as any).interpretation || '';
  const notes = (workerResult as any).notes || '';

  // RIS 결과인 경우
  const findings = (workerResult as any).findings || '';
  const impression = (workerResult as any).impression || '';
  const recommendation = (workerResult as any).recommendation || '';

  // 확정 정보
  const verifiedAt = (workerResult as any)._verifiedAt || ocs.confirmed_at;
  const verifiedBy = (workerResult as any)._verifiedBy || ocs.worker?.name;

  return (
    <div className="ocs-result-report">
      {/* 헤더 (인쇄 시 숨김) */}
      <div className="report-actions no-print">
        <button className="btn btn-secondary" onClick={handleBack}>
          돌아가기
        </button>
        <button className="btn btn-primary" onClick={handlePrint}>
          인쇄
        </button>
      </div>

      {/* 보고서 본문 */}
      <div className="report-container">
        {/* 보고서 헤더 */}
        <header className="report-header">
          <h1>검사 결과 보고서</h1>
          <div className="report-meta">
            <span className="report-id">{ocs.ocs_id}</span>
            <span className={`report-type ${ocs.job_role.toLowerCase()}`}>
              {ocs.job_role === 'RIS' ? '영상검사' :
               ocs.job_role === 'LIS' ? '임상검사' :
               ocs.job_role}
            </span>
          </div>
        </header>

        {/* 환자 정보 */}
        <section className="report-section patient-section">
          <h2>환자 정보</h2>
          <div className="info-grid">
            <div className="info-item">
              <label>환자번호</label>
              <span>{ocs.patient.patient_number}</span>
            </div>
            <div className="info-item">
              <label>환자명</label>
              <span>{ocs.patient.name}</span>
            </div>
            <div className="info-item">
              <label>검사일</label>
              <span>{formatDateOnly(ocs.in_progress_at || ocs.accepted_at)}</span>
            </div>
            <div className="info-item">
              <label>보고일</label>
              <span>{formatDateOnly(ocs.confirmed_at)}</span>
            </div>
          </div>
        </section>

        {/* 검사 정보 */}
        <section className="report-section order-section">
          <h2>검사 정보</h2>
          <div className="info-grid">
            <div className="info-item">
              <label>검사 유형</label>
              <span>{ocs.job_type}</span>
            </div>
            <div className="info-item">
              <label>처방 의사</label>
              <span>{ocs.doctor.name}</span>
            </div>
            <div className="info-item">
              <label>검사 담당자</label>
              <span>{ocs.worker?.name || '-'}</span>
            </div>
            <div className="info-item">
              <label>우선순위</label>
              <span className={`priority-tag priority-${ocs.priority}`}>
                {ocs.priority_display}
              </span>
            </div>
          </div>

          {/* 의사 요청 사항 */}
          {ocs.doctor_request && Object.keys(ocs.doctor_request).length > 0 && (
            <div className="request-info">
              <h3>의사 요청 사항</h3>
              {(ocs.doctor_request as any).clinical_info && (
                <div className="request-item">
                  <label>임상 정보:</label>
                  <p>{(ocs.doctor_request as any).clinical_info}</p>
                </div>
              )}
              {(ocs.doctor_request as any).special_instruction && (
                <div className="request-item">
                  <label>특별 지시:</label>
                  <p>{(ocs.doctor_request as any).special_instruction}</p>
                </div>
              )}
            </div>
          )}
        </section>

        {/* 검사 결과 */}
        <section className="report-section result-section">
          <h2>검사 결과</h2>

          {/* LIS 결과 - 테이블 형식 */}
          {ocs.job_role === 'LIS' && labResults.length > 0 && (
            <div className="lab-results">
              <table className="result-table">
                <thead>
                  <tr>
                    <th>검사 항목</th>
                    <th>결과</th>
                    <th>단위</th>
                    <th>참고치</th>
                    <th>판정</th>
                  </tr>
                </thead>
                <tbody>
                  {labResults.map((item: any, index: number) => (
                    <tr
                      key={index}
                      className={
                        item.flag === 'critical' ? 'row-critical' :
                        item.flag === 'abnormal' ? 'row-abnormal' : ''
                      }
                    >
                      <td>{item.testName}</td>
                      <td className="result-value">{item.value}</td>
                      <td>{item.unit}</td>
                      <td>{item.refRange}</td>
                      <td>
                        <span className={`flag flag-${item.flag}`}>
                          {item.flag === 'normal' ? '정상' :
                           item.flag === 'abnormal' ? '비정상' :
                           item.flag === 'critical' ? '위험' : item.flag}
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}

          {/* RIS 결과 - 텍스트 형식 */}
          {ocs.job_role === 'RIS' && (
            <div className="imaging-results">
              {findings && (
                <div className="result-block">
                  <h3>소견 (Findings)</h3>
                  <p className="result-text">{findings}</p>
                </div>
              )}
              {impression && (
                <div className="result-block">
                  <h3>인상 (Impression)</h3>
                  <p className="result-text">{impression}</p>
                </div>
              )}
              {recommendation && (
                <div className="result-block">
                  <h3>권고 사항 (Recommendation)</h3>
                  <p className="result-text">{recommendation}</p>
                </div>
              )}
            </div>
          )}

          {/* 해석/종합 소견 */}
          {interpretation && (
            <div className="result-block interpretation">
              <h3>의학적 해석</h3>
              <p className="result-text">{interpretation}</p>
            </div>
          )}

          {/* 비고 */}
          {notes && (
            <div className="result-block notes">
              <h3>비고</h3>
              <p className="result-text">{notes}</p>
            </div>
          )}

          {/* 결과가 없는 경우 JSON 표시 */}
          {labResults.length === 0 && !findings && !impression && !interpretation && (
            <div className="raw-result">
              <h3>검사 결과 데이터</h3>
              <pre className="json-viewer">
                {JSON.stringify(workerResult, null, 2)}
              </pre>
            </div>
          )}
        </section>

        {/* 확정 정보 */}
        <section className="report-section confirmation-section">
          <div className="confirmation-info">
            <div className="confirmation-item">
              <label>확정일시</label>
              <span>{formatDate(ocs.confirmed_at)}</span>
            </div>
            <div className="confirmation-item">
              <label>확정자</label>
              <span>{verifiedBy || '-'}</span>
            </div>
            <div className="confirmation-item">
              <label>결과 상태</label>
              <span className={`result-status ${ocs.ocs_result ? 'normal' : 'abnormal'}`}>
                {ocs.ocs_result ? '정상' : '비정상'}
              </span>
            </div>
          </div>
        </section>

        {/* 보고서 푸터 */}
        <footer className="report-footer">
          <p>본 보고서는 의료 목적으로만 사용되어야 하며, 의료 전문가의 해석이 필요합니다.</p>
          <p className="print-date">출력일시: {new Date().toLocaleString('ko-KR')}</p>
        </footer>
      </div>
    </div>
  );
}

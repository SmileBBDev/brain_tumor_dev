/**
 * RIS Study 상세 페이지 (P.75-80)
 * - 환자 정보 + Study 정보 + AI 분석 요약
 * - 판독 리포트 작성/조회/수정
 * - 검사 결과 항목 추가 기능
 * - Final 확정, EMR 전송, PDF 출력
 */
import { useState, useEffect, useRef } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useAuth } from '../auth/AuthProvider';
import { getOCS, startOCS, saveOCSResult, confirmOCS } from '@/services/ocs.api';
import type { OCSDetail, RISWorkerResult } from '@/types/ocs';
import { OCS_STATUS_LABELS } from '@/types/ocs';
import AIAnalysisPanel from './components/AIAnalysisPanel';
import DicomViewerPopup from '@/components/DicomViewerPopup';
import './RISStudyDetailPage.css';

// 검사 결과 항목 타입
interface ImageResultItem {
  itemName: string;
  value: string;
  unit: string;
  refRange: string;
  flag: 'normal' | 'abnormal' | 'critical';
}

// 업로드 파일 타입
interface UploadedFile {
  name: string;
  size: number;
  type: string;
  uploadedAt: string;
  dataUrl?: string;
}

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

// 탭 타입
type TabType = 'info' | 'report' | 'result' | 'history';

export default function RISStudyDetailPage() {
  const { ocsId } = useParams<{ ocsId: string }>();
  const navigate = useNavigate();
  const { user } = useAuth();

  const [ocsDetail, setOcsDetail] = useState<OCSDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState<TabType>('info');
  const [saving, setSaving] = useState(false);

  // Report form state
  const [findings, setFindings] = useState('');
  const [impression, setImpression] = useState('');
  const [recommendation, setRecommendation] = useState('');

  // 검사 결과 항목
  const [imageResults, setImageResults] = useState<ImageResultItem[]>([]);

  // 파일 업로드
  const [uploadedFiles, setUploadedFiles] = useState<UploadedFile[]>([]);
  const fileInputRef = useRef<HTMLInputElement>(null);

  // DICOM 뷰어 팝업
  const [viewerOpen, setViewerOpen] = useState(false);

  // OCS 상세 조회
  useEffect(() => {
    const fetchDetail = async () => {
      if (!ocsId) return;
      setLoading(true);
      try {
        const data = await getOCS(Number(ocsId));
        setOcsDetail(data);

        // 기존 결과가 있으면 폼에 로드
        if (data.worker_result && data.worker_result._template === 'RIS') {
          const result = data.worker_result as RISWorkerResult;
          setFindings(result.findings || '');
          setImpression(result.impression || '');
          setRecommendation(result.recommendation || '');
          // 검사 결과 항목 로드
          if ((result as any).imageResults) {
            setImageResults((result as any).imageResults as ImageResultItem[]);
          }
          // 파일 로드
          if ((result as any).files) {
            setUploadedFiles((result as any).files as UploadedFile[]);
          }
        }
      } catch (error) {
        console.error('Failed to fetch OCS detail:', error);
        alert('상세 정보를 불러오는데 실패했습니다.');
      } finally {
        setLoading(false);
      }
    };

    fetchDetail();
  }, [ocsId]);

  // 결과 항목 추가
  const handleAddResult = () => {
    setImageResults([
      ...imageResults,
      { itemName: '', value: '', unit: '', refRange: '', flag: 'normal' },
    ]);
  };

  // 결과 항목 변경
  const handleResultChange = (index: number, field: keyof ImageResultItem, value: string) => {
    const updated = [...imageResults];
    updated[index] = { ...updated[index], [field]: value };
    setImageResults(updated);
  };

  // 결과 항목 삭제
  const handleRemoveResult = (index: number) => {
    setImageResults(imageResults.filter((_, i) => i !== index));
  };

  // 파일 업로드 핸들러
  const handleFileUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = e.target.files;
    if (!files) return;

    Array.from(files).forEach((file) => {
      const reader = new FileReader();
      reader.onload = () => {
        const newFile: UploadedFile = {
          name: file.name,
          size: file.size,
          type: file.type,
          uploadedAt: new Date().toISOString(),
          dataUrl: reader.result as string,
        };
        setUploadedFiles((prev) => [...prev, newFile]);
      };
      reader.readAsDataURL(file);
    });

    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  };

  // 파일 삭제
  const handleRemoveFile = (index: number) => {
    setUploadedFiles(uploadedFiles.filter((_, i) => i !== index));
  };

  // 파일 크기 포맷
  const formatFileSize = (bytes: number): string => {
    if (bytes < 1024) return bytes + ' B';
    if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB';
    return (bytes / (1024 * 1024)).toFixed(1) + ' MB';
  };

  // 판독 시작
  const handleStartReading = async () => {
    if (!ocsDetail) return;
    try {
      await startOCS(ocsDetail.id);
      // 상태 갱신
      const updated = await getOCS(ocsDetail.id);
      setOcsDetail(updated);
      setActiveTab('report');
      alert('판독을 시작합니다.');
    } catch (error) {
      console.error('Failed to start reading:', error);
      alert('판독 시작에 실패했습니다.');
    }
  };

  // 임시 저장
  const handleSaveDraft = async () => {
    if (!ocsDetail) return;
    setSaving(true);
    try {
      const workerResult = {
        _template: 'RIS',
        _version: '1.0',
        _confirmed: false,
        findings,
        impression,
        recommendation,
        imageResults,
        files: uploadedFiles,
        dicom: (ocsDetail.worker_result as RISWorkerResult)?.dicom || {
          study_uid: '',
          series: [],
          accession_number: '',
        },
        _custom: {},
        _savedAt: new Date().toISOString(),
      };

      await saveOCSResult(ocsDetail.id, { worker_result: workerResult });
      alert('임시 저장되었습니다.');

      // 상태 갱신
      const updated = await getOCS(ocsDetail.id);
      setOcsDetail(updated);
    } catch (error) {
      console.error('Failed to save draft:', error);
      alert('저장에 실패했습니다.');
    } finally {
      setSaving(false);
    }
  };

  // Final 저장 (결과 제출 및 확정)
  const handleSubmitFinal = async () => {
    if (!ocsDetail) return;

    if (!findings.trim() || !impression.trim()) {
      alert('판독 소견과 결론은 필수 입력입니다.');
      return;
    }

    if (!confirm('Final 저장 후에는 수정이 불가능합니다. 계속하시겠습니까?')) {
      return;
    }

    setSaving(true);
    try {
      const workerResult = {
        _template: 'RIS',
        _version: '1.0',
        _confirmed: true,
        findings,
        impression,
        recommendation,
        imageResults,
        files: uploadedFiles,
        dicom: (ocsDetail.worker_result as RISWorkerResult)?.dicom || {
          study_uid: '',
          series: [],
          accession_number: '',
        },
        _custom: {},
        _verifiedAt: new Date().toISOString(),
        _verifiedBy: user?.name,
      };

      // RIS도 결과 제출 시 바로 확정 처리
      await confirmOCS(ocsDetail.id, { worker_result: workerResult });
      alert('Final 저장 및 확정이 완료되었습니다.');

      // 상태 갱신
      const updated = await getOCS(ocsDetail.id);
      setOcsDetail(updated);
    } catch (error) {
      console.error('Failed to submit final:', error);
      alert('Final 저장에 실패했습니다.');
    } finally {
      setSaving(false);
    }
  };

  // EMR 전송 (목업)
  const handleSendToEMR = () => {
    alert('EMR 전송 기능은 준비 중입니다.');
  };

  // PDF 출력 (목업)
  const handleExportPDF = () => {
    alert('PDF 출력 기능은 준비 중입니다.');
  };

  // DICOM Viewer 열기
  const handleOpenViewer = () => {
    setViewerOpen(true);
  };

  if (loading) {
    return <div className="page ris-study-detail loading">로딩 중...</div>;
  }

  if (!ocsDetail) {
    return <div className="page ris-study-detail error">데이터를 찾을 수 없습니다.</div>;
  }

  const isMyWork = ocsDetail.worker?.id === user?.id;
  const canEdit = isMyWork && ['ACCEPTED', 'IN_PROGRESS'].includes(ocsDetail.ocs_status);
  const isFinalized = ['RESULT_READY', 'CONFIRMED'].includes(ocsDetail.ocs_status);
  const workerResult = ocsDetail.worker_result as RISWorkerResult | null;

  return (
    <div className="page ris-study-detail">
      {/* 헤더 */}
      <header className="detail-header">
        <div className="header-left">
          <button className="btn btn-back" onClick={() => navigate(-1)}>
            &larr; 목록으로
          </button>
          <h2>영상 판독 상세</h2>
          <span className={`status-badge status-${ocsDetail.ocs_status.toLowerCase()}`}>
            {OCS_STATUS_LABELS[ocsDetail.ocs_status]}
          </span>
        </div>
        <div className="header-right">
          {ocsDetail.ocs_status === 'ACCEPTED' && isMyWork && (
            <button className="btn btn-primary" onClick={handleStartReading}>
              판독 시작
            </button>
          )}
          {ocsDetail.ocs_status === 'ORDERED' && (
            <span className="info-text">접수 대기 중</span>
          )}
          {canEdit && !isFinalized && (
            <>
              <button
                className="btn btn-secondary"
                onClick={handleSaveDraft}
                disabled={saving}
              >
                {saving ? '저장 중...' : '임시 저장'}
              </button>
              <button
                className="btn btn-primary"
                onClick={handleSubmitFinal}
                disabled={saving}
              >
                {saving ? '저장 중...' : '결과 제출'}
              </button>
            </>
          )}
          {isFinalized && (
            <>
              <button className="btn btn-success" onClick={handleSendToEMR}>
                EMR 전송
              </button>
              <button className="btn btn-secondary" onClick={handleExportPDF}>
                PDF 출력
              </button>
            </>
          )}
        </div>
      </header>

      {/* 환자 정보 바 */}
      <section className="patient-info-bar">
        <div className="info-item">
          <label>환자명</label>
          <span>{ocsDetail.patient.name}</span>
        </div>
        <div className="info-item">
          <label>환자번호</label>
          <span>{ocsDetail.patient.patient_number}</span>
        </div>
        <div className="info-item">
          <label>검사 유형</label>
          <span>{ocsDetail.job_type}</span>
        </div>
        <div className="info-item">
          <label>처방 의사</label>
          <span>{ocsDetail.doctor.name}</span>
        </div>
        <div className="info-item">
          <label>처방일시</label>
          <span>{formatDate(ocsDetail.created_at)}</span>
        </div>
        <div className="info-item">
          <label>담당자</label>
          <span>{ocsDetail.worker?.name || '미배정'}</span>
        </div>
      </section>

      {/* 탭 영역 */}
      <nav className="tab-nav">
        <button
          className={`tab-btn ${activeTab === 'info' ? 'active' : ''}`}
          onClick={() => setActiveTab('info')}
        >
          검사 정보
        </button>
        <button
          className={`tab-btn ${activeTab === 'report' ? 'active' : ''}`}
          onClick={() => setActiveTab('report')}
        >
          판독 리포트
        </button>
        <button
          className={`tab-btn ${activeTab === 'result' ? 'active' : ''}`}
          onClick={() => setActiveTab('result')}
        >
          검사 결과
        </button>
        <button
          className={`tab-btn ${activeTab === 'history' ? 'active' : ''}`}
          onClick={() => setActiveTab('history')}
        >
          이력
        </button>
      </nav>

      {/* 탭 콘텐츠 */}
      <div className="tab-content">
        {/* 검사 정보 탭 */}
        {activeTab === 'info' && (
          <div className="tab-panel info-panel">
            <div className="panel-row">
              {/* 좌측: 오더 정보 */}
              <div className="panel-section order-info">
                <h3>오더 정보</h3>
                <div className="info-grid">
                  <div className="info-row">
                    <label>OCS ID</label>
                    <span>{ocsDetail.ocs_id}</span>
                  </div>
                  <div className="info-row">
                    <label>우선순위</label>
                    <span className={`priority-badge priority-${ocsDetail.priority}`}>
                      {ocsDetail.priority_display}
                    </span>
                  </div>
                  <div className="info-row">
                    <label>주호소</label>
                    <span>{ocsDetail.doctor_request?.chief_complaint || '-'}</span>
                  </div>
                  <div className="info-row">
                    <label>임상 정보</label>
                    <span>{ocsDetail.doctor_request?.clinical_info || '-'}</span>
                  </div>
                  <div className="info-row">
                    <label>검사 요청</label>
                    <span>{ocsDetail.doctor_request?.request_detail || '-'}</span>
                  </div>
                  <div className="info-row">
                    <label>특별 지시</label>
                    <span>{ocsDetail.doctor_request?.special_instruction || '-'}</span>
                  </div>
                </div>
              </div>

              {/* 우측: AI 분석 결과 */}
              <div className="panel-section ai-section">
                <AIAnalysisPanel ocsId={ocsDetail.id} jobType={ocsDetail.job_type} />
              </div>
            </div>

            {/* DICOM 정보 */}
            {workerResult?.dicom && (
              <div className="panel-section dicom-info">
                <h3>DICOM 정보</h3>
                <div className="info-grid">
                  <div className="info-row">
                    <label>Study UID</label>
                    <span>{workerResult.dicom.study_uid || '-'}</span>
                  </div>
                  <div className="info-row">
                    <label>Accession Number</label>
                    <span>{workerResult.dicom.accession_number || '-'}</span>
                  </div>
                  {workerResult.dicom.series?.length > 0 && (
                    <div className="info-row series-row">
                      <label>Series</label>
                      <div className="series-list">
                        {workerResult.dicom.series.map((s, idx) => (
                          <div key={idx} className="series-item">
                            <span className="modality">{s.modality}</span>
                            <span className="desc">{s.description}</span>
                            <span className="count">{s.instance_count}장</span>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              </div>
            )}
          </div>
        )}

        {/* 판독 리포트 탭 */}
        {activeTab === 'report' && (
          <div className="tab-panel report-panel">
            {/* 판독 폼 */}
            <div className="report-form">
              <div className="form-group">
                <label>판독 소견 (Findings) *</label>
                <textarea
                  value={findings}
                  onChange={(e) => setFindings(e.target.value)}
                  placeholder="영상에서 관찰된 소견을 입력하세요..."
                  rows={6}
                  disabled={!canEdit || isFinalized}
                />
              </div>

              <div className="form-group">
                <label>판독 결론 (Impression) *</label>
                <textarea
                  value={impression}
                  onChange={(e) => setImpression(e.target.value)}
                  placeholder="최종 판독 결론을 입력하세요..."
                  rows={4}
                  disabled={!canEdit || isFinalized}
                />
              </div>

              <div className="form-group">
                <label>권고 사항 (Recommendation)</label>
                <textarea
                  value={recommendation}
                  onChange={(e) => setRecommendation(e.target.value)}
                  placeholder="추가 검사 권고 등..."
                  rows={2}
                  disabled={!canEdit || isFinalized}
                />
              </div>

              {isFinalized && (
                <div className="finalized-info">
                  <p>이 리포트는 Final 저장되어 수정이 불가능합니다.</p>
                  <p>확정일시: {formatDate(ocsDetail.result_ready_at)}</p>
                </div>
              )}
            </div>

            {/* 우측: AI 분석 미리보기 */}
            <div className="ai-preview">
              <AIAnalysisPanel
                ocsId={ocsDetail.id}
                jobType={ocsDetail.job_type}
                compact
              />
            </div>
          </div>
        )}

        {/* 검사 결과 탭 */}
        {activeTab === 'result' && (
          <div className="tab-panel result-panel">
            {/* 영상 조회 섹션 */}
            <div className="viewer-section">
              <button className="btn btn-secondary" onClick={handleOpenViewer}>
                영상 조회
              </button>
            </div>

            {/* 파일 업로드 섹션 */}
            <div className="file-upload-section">
              <div className="section-header">
                <h3>결과 파일 첨부</h3>
                {canEdit && (
                  <>
                    <input
                      ref={fileInputRef}
                      type="file"
                      multiple
                      accept=".pdf,.jpg,.jpeg,.png,.dcm,.dicom"
                      onChange={handleFileUpload}
                      style={{ display: 'none' }}
                      id="ris-file-upload"
                    />
                    <label htmlFor="ris-file-upload" className="btn btn-secondary btn-sm">
                      파일 선택
                    </label>
                  </>
                )}
              </div>

              {uploadedFiles.length > 0 ? (
                <ul className="file-list">
                  {uploadedFiles.map((file, index) => (
                    <li key={index} className="file-item">
                      <span className="file-icon">
                        {file.type.includes('pdf') ? '📄' :
                         file.type.includes('image') ? '🖼️' :
                         file.type.includes('dicom') ? '🩻' : '📎'}
                      </span>
                      <span className="file-name">{file.name}</span>
                      <span className="file-size">{formatFileSize(file.size)}</span>
                      {canEdit && (
                        <button
                          className="btn btn-sm btn-danger"
                          onClick={() => handleRemoveFile(index)}
                        >
                          삭제
                        </button>
                      )}
                    </li>
                  ))}
                </ul>
              ) : (
                <div className="no-files">
                  첨부된 파일이 없습니다. {canEdit && '파일을 업로드하세요.'}
                </div>
              )}
            </div>

            {/* 검사 결과 항목 */}
            <div className="result-items-section">
              <div className="section-header">
                <h3>검사 결과 입력</h3>
                {canEdit && (
                  <button className="btn btn-primary btn-sm" onClick={handleAddResult}>
                    + 항목 추가
                  </button>
                )}
              </div>

              <table className="result-table">
                <thead>
                  <tr>
                    <th>검사 항목</th>
                    <th>결과값</th>
                    <th>단위</th>
                    <th>참고 범위</th>
                    <th>판정</th>
                    {canEdit && <th>삭제</th>}
                  </tr>
                </thead>
                <tbody>
                  {imageResults.length === 0 ? (
                    <tr>
                      <td colSpan={canEdit ? 6 : 5} className="empty">
                        검사 결과가 없습니다.
                        {canEdit && ' "항목 추가" 버튼을 클릭하여 결과를 입력하세요.'}
                      </td>
                    </tr>
                  ) : (
                    imageResults.map((result, index) => (
                      <tr key={index} className={result.flag !== 'normal' ? `row-${result.flag}` : ''}>
                        <td>
                          {canEdit ? (
                            <input
                              type="text"
                              value={result.itemName}
                              onChange={(e) => handleResultChange(index, 'itemName', e.target.value)}
                              placeholder="검사 항목명"
                            />
                          ) : (
                            result.itemName
                          )}
                        </td>
                        <td>
                          {canEdit ? (
                            <input
                              type="text"
                              value={result.value}
                              onChange={(e) => handleResultChange(index, 'value', e.target.value)}
                              placeholder="결과값"
                            />
                          ) : (
                            result.value
                          )}
                        </td>
                        <td>
                          {canEdit ? (
                            <input
                              type="text"
                              value={result.unit}
                              onChange={(e) => handleResultChange(index, 'unit', e.target.value)}
                              placeholder="단위"
                            />
                          ) : (
                            result.unit
                          )}
                        </td>
                        <td>
                          {canEdit ? (
                            <input
                              type="text"
                              value={result.refRange}
                              onChange={(e) => handleResultChange(index, 'refRange', e.target.value)}
                              placeholder="참고 범위"
                            />
                          ) : (
                            result.refRange
                          )}
                        </td>
                        <td>
                          {canEdit ? (
                            <select
                              value={result.flag}
                              onChange={(e) =>
                                handleResultChange(index, 'flag', e.target.value as ImageResultItem['flag'])
                              }
                            >
                              <option value="normal">정상</option>
                              <option value="abnormal">이상</option>
                              <option value="critical">Critical</option>
                            </select>
                          ) : (
                            <span className={`flag flag-${result.flag}`}>
                              {result.flag === 'normal' ? '정상' : result.flag === 'abnormal' ? '이상' : 'Critical'}
                            </span>
                          )}
                        </td>
                        {canEdit && (
                          <td>
                            <button
                              className="btn btn-sm btn-danger"
                              onClick={() => handleRemoveResult(index)}
                            >
                              삭제
                            </button>
                          </td>
                        )}
                      </tr>
                    ))
                  )}
                </tbody>
              </table>
            </div>
          </div>
        )}

        {/* 이력 탭 */}
        {activeTab === 'history' && (
          <div className="tab-panel history-panel">
            <h3>변경 이력</h3>
            {ocsDetail.history?.length > 0 ? (
              <table className="history-table">
                <thead>
                  <tr>
                    <th>일시</th>
                    <th>액션</th>
                    <th>수행자</th>
                    <th>이전 상태</th>
                    <th>이후 상태</th>
                    <th>비고</th>
                  </tr>
                </thead>
                <tbody>
                  {ocsDetail.history.map((h) => (
                    <tr key={h.id}>
                      <td>{formatDate(h.created_at)}</td>
                      <td>{h.action_display}</td>
                      <td>{h.actor?.name || '-'}</td>
                      <td>{h.from_status ? OCS_STATUS_LABELS[h.from_status] : '-'}</td>
                      <td>{h.to_status ? OCS_STATUS_LABELS[h.to_status] : '-'}</td>
                      <td>{h.reason || '-'}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            ) : (
              <p className="no-data">이력이 없습니다.</p>
            )}
          </div>
        )}
      </div>

      {/* DICOM 영상 조회 팝업 */}
      <DicomViewerPopup open={viewerOpen} onClose={() => setViewerOpen(false)} />
    </div>
  );
}

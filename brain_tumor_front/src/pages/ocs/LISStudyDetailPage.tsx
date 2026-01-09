/**
 * LIS 검사 상세 페이지 (P.87-89)
 * - 환자 정보 및 검사 결과 상세
 * - 결과 검증 및 보고 확정
 * - 의학적 해석(Interpretation) 입력
 * - 파일 업로드 기능
 */
import { useState, useEffect, useCallback, useRef } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useAuth } from '../auth/AuthProvider';
import { getOCS, startOCS, saveOCSResult, confirmOCS } from '@/services/ocs.api';
import type { OCSDetail } from '@/types/ocs';
import './LISStudyDetailPage.css';

// 탭 타입
type TabType = 'info' | 'result' | 'interpretation' | 'history';

// 검사 결과 항목 타입
interface LabResultItem {
  testName: string;
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
  dataUrl?: string; // Base64로 저장 (실제로는 서버 업로드 필요)
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

// Flag 표시
const getFlagDisplay = (flag: string) => {
  switch (flag) {
    case 'critical':
      return <span className="flag flag-critical">Critical</span>;
    case 'abnormal':
      return <span className="flag flag-abnormal">이상</span>;
    default:
      return <span className="flag flag-normal">정상</span>;
  }
};

export default function LISStudyDetailPage() {
  const { ocsId } = useParams<{ ocsId: string }>();
  const navigate = useNavigate();
  const { user } = useAuth();

  const [ocs, setOcs] = useState<OCSDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [activeTab, setActiveTab] = useState<TabType>('info');

  // 결과 입력 폼
  const [labResults, setLabResults] = useState<LabResultItem[]>([]);
  const [interpretation, setInterpretation] = useState('');
  const [notes, setNotes] = useState('');

  // 파일 업로드
  const [uploadedFiles, setUploadedFiles] = useState<UploadedFile[]>([]);
  const fileInputRef = useRef<HTMLInputElement>(null);

  // 데이터 로드
  const fetchOCSDetail = useCallback(async () => {
    if (!ocsId) return;

    setLoading(true);
    try {
      const data = await getOCS(parseInt(ocsId));
      setOcs(data);

      // 기존 결과가 있으면 폼에 로드
      if (data.worker_result) {
        const result = data.worker_result as Record<string, unknown>;
        if (result.labResults) {
          setLabResults(result.labResults as LabResultItem[]);
        }
        if (result.interpretation) {
          setInterpretation(result.interpretation as string);
        }
        if (result.notes) {
          setNotes(result.notes as string);
        }
        if (result.files) {
          setUploadedFiles(result.files as UploadedFile[]);
        }
      }
    } catch (error) {
      console.error('Failed to fetch OCS detail:', error);
      alert('검사 정보를 불러오는데 실패했습니다.');
    } finally {
      setLoading(false);
    }
  }, [ocsId]);

  useEffect(() => {
    fetchOCSDetail();
  }, [fetchOCSDetail]);

  // 권한 체크
  const isWorker = ocs?.worker?.id === user?.id;
  const canEdit = isWorker && ['ACCEPTED', 'IN_PROGRESS'].includes(ocs?.ocs_status || '');
  const canVerify = isWorker && ocs?.ocs_status === 'IN_PROGRESS';

  // 작업 시작
  const handleStart = async () => {
    if (!ocs) return;
    try {
      await startOCS(ocs.id);
      await fetchOCSDetail();
    } catch (error) {
      console.error('Failed to start OCS:', error);
      alert('작업 시작에 실패했습니다.');
    }
  };

  // 결과 항목 추가
  const handleAddResult = () => {
    setLabResults([
      ...labResults,
      { testName: '', value: '', unit: '', refRange: '', flag: 'normal' },
    ]);
  };

  // 결과 항목 변경
  const handleResultChange = (index: number, field: keyof LabResultItem, value: string) => {
    const updated = [...labResults];
    updated[index] = { ...updated[index], [field]: value };
    setLabResults(updated);
  };

  // 결과 항목 삭제
  const handleRemoveResult = (index: number) => {
    setLabResults(labResults.filter((_, i) => i !== index));
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

    // 입력 초기화
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

  // 임시 저장
  const handleSave = async () => {
    if (!ocs) return;

    setSaving(true);
    try {
      await saveOCSResult(ocs.id, {
        worker_result: {
          labResults,
          interpretation,
          notes,
          files: uploadedFiles,
          _savedAt: new Date().toISOString(),
        },
      });
      alert('임시 저장되었습니다.');
      await fetchOCSDetail();
    } catch (error) {
      console.error('Failed to save result:', error);
      alert('저장에 실패했습니다.');
    } finally {
      setSaving(false);
    }
  };

  // 결과 제출 및 확정 (IN_PROGRESS → CONFIRMED)
  const handleSubmit = async () => {
    if (!ocs) return;

    // 검증
    if (labResults.length === 0) {
      alert('검사 결과를 입력해주세요.');
      return;
    }

    const hasCritical = labResults.some((r) => r.flag === 'critical');
    if (hasCritical && !interpretation) {
      alert('Critical 결과가 있습니다. 해석(Interpretation)을 입력해주세요.');
      return;
    }

    if (!confirm('결과를 제출하시겠습니까? 제출 후에는 수정이 제한됩니다.')) {
      return;
    }

    setSaving(true);
    try {
      // LIS는 결과 제출 시 바로 확정 처리
      await confirmOCS(ocs.id, {
        worker_result: {
          labResults,
          interpretation,
          notes,
          files: uploadedFiles,
          _verifiedAt: new Date().toISOString(),
          _verifiedBy: user?.name,
        },
      });
      alert('결과가 제출되고 확정되었습니다.');
      await fetchOCSDetail();
    } catch (error) {
      console.error('Failed to submit result:', error);
      alert('제출에 실패했습니다.');
    } finally {
      setSaving(false);
    }
  };

  if (loading) {
    return <div className="page lis-detail-page loading">로딩 중...</div>;
  }

  if (!ocs) {
    return <div className="page lis-detail-page error">검사 정보를 찾을 수 없습니다.</div>;
  }

  // 이상 항목 수
  const abnormalCount = labResults.filter((r) => r.flag === 'abnormal').length;
  const criticalCount = labResults.filter((r) => r.flag === 'critical').length;

  return (
    <div className="page lis-detail-page">
      {/* 헤더 */}
      <header className="detail-header">
        <button className="btn-back" onClick={() => navigate(-1)}>
          &larr; 목록으로
        </button>
        <div className="header-info">
          <h2>검사 상세 - {ocs.ocs_id}</h2>
          <span className={`status-badge status-${ocs.ocs_status.toLowerCase()}`}>
            {ocs.ocs_status_display}
          </span>
        </div>
        <div className="header-actions">
          {ocs.ocs_status === 'ACCEPTED' && isWorker && (
            <button className="btn btn-primary" onClick={handleStart}>
              작업 시작
            </button>
          )}
          {canEdit && (
            <>
              <button className="btn btn-secondary" onClick={handleSave} disabled={saving}>
                임시 저장
              </button>
              {canVerify && (
                <button className="btn btn-success" onClick={handleSubmit} disabled={saving}>
                  결과 제출
                </button>
              )}
            </>
          )}
        </div>
      </header>

      {/* 환자 정보 바 */}
      <section className="patient-info-bar">
        <div className="info-item">
          <label>환자명</label>
          <span>{ocs.patient.name}</span>
        </div>
        <div className="info-item">
          <label>환자번호</label>
          <span>{ocs.patient.patient_number}</span>
        </div>
        <div className="info-item">
          <label>검사 항목</label>
          <span>{ocs.job_type}</span>
        </div>
        <div className="info-item">
          <label>처방 의사</label>
          <span>{ocs.doctor.name}</span>
        </div>
        <div className="info-item">
          <label>처방일</label>
          <span>{formatDate(ocs.created_at)}</span>
        </div>
        <div className="info-item">
          <label>우선순위</label>
          <span className={`priority priority-${ocs.priority}`}>{ocs.priority_display}</span>
        </div>
      </section>

      {/* 결과 요약 */}
      {labResults.length > 0 && (
        <section className="result-summary">
          <div className="summary-card">
            <span className="count">{labResults.length}</span>
            <span className="label">전체 항목</span>
          </div>
          <div className="summary-card abnormal">
            <span className="count">{abnormalCount}</span>
            <span className="label">이상 항목</span>
          </div>
          <div className="summary-card critical">
            <span className="count">{criticalCount}</span>
            <span className="label">Critical</span>
          </div>
        </section>
      )}

      {/* 탭 메뉴 */}
      <nav className="tab-nav">
        <button
          className={activeTab === 'info' ? 'active' : ''}
          onClick={() => setActiveTab('info')}
        >
          검사 정보
        </button>
        <button
          className={activeTab === 'result' ? 'active' : ''}
          onClick={() => setActiveTab('result')}
        >
          검사 결과
        </button>
        <button
          className={activeTab === 'interpretation' ? 'active' : ''}
          onClick={() => setActiveTab('interpretation')}
        >
          해석/소견
        </button>
        <button
          className={activeTab === 'history' ? 'active' : ''}
          onClick={() => setActiveTab('history')}
        >
          이력
        </button>
      </nav>

      {/* 탭 콘텐츠 */}
      <section className="tab-content">
        {/* 검사 정보 탭 */}
        {activeTab === 'info' && (
          <div className="info-tab">
            <div className="info-grid">
              <div className="info-row">
                <label>OCS ID</label>
                <span>{ocs.ocs_id}</span>
              </div>
              <div className="info-row">
                <label>검사 유형</label>
                <span>{ocs.job_type}</span>
              </div>
              <div className="info-row">
                <label>상태</label>
                <span>{ocs.ocs_status_display}</span>
              </div>
              <div className="info-row">
                <label>담당자</label>
                <span>{ocs.worker?.name || '미배정'}</span>
              </div>
              <div className="info-row">
                <label>접수일시</label>
                <span>{formatDate(ocs.accepted_at)}</span>
              </div>
              <div className="info-row">
                <label>작업시작</label>
                <span>{formatDate(ocs.in_progress_at)}</span>
              </div>
              <div className="info-row">
                <label>결과제출</label>
                <span>{formatDate(ocs.result_ready_at)}</span>
              </div>
            </div>

            {/* 의사 요청 사항 */}
            <div className="doctor-request">
              <h4>의사 요청 사항</h4>
              <pre>{JSON.stringify(ocs.doctor_request, null, 2)}</pre>
            </div>
          </div>
        )}

        {/* 검사 결과 탭 */}
        {activeTab === 'result' && (
          <div className="result-tab">
            {/* 파일 업로드 섹션 */}
            <div className="file-upload-section">
              <div className="section-header">
                <h4>결과 파일 첨부</h4>
                {canEdit && (
                  <>
                    <input
                      ref={fileInputRef}
                      type="file"
                      multiple
                      accept=".pdf,.jpg,.jpeg,.png,.xlsx,.xls,.csv,.doc,.docx"
                      onChange={handleFileUpload}
                      style={{ display: 'none' }}
                      id="file-upload"
                    />
                    <label htmlFor="file-upload" className="btn btn-sm btn-secondary">
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
                         file.type.includes('sheet') || file.type.includes('excel') ? '📊' : '📎'}
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

            <div className="result-header">
              <h4>검사 결과 입력</h4>
              {canEdit && (
                <button className="btn btn-sm btn-primary" onClick={handleAddResult}>
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
                {labResults.length === 0 ? (
                  <tr>
                    <td colSpan={canEdit ? 6 : 5} className="empty">
                      검사 결과가 없습니다.
                      {canEdit && ' "항목 추가" 버튼을 클릭하여 결과를 입력하세요.'}
                    </td>
                  </tr>
                ) : (
                  labResults.map((result, index) => (
                    <tr key={index} className={result.flag !== 'normal' ? `row-${result.flag}` : ''}>
                      <td>
                        {canEdit ? (
                          <input
                            type="text"
                            value={result.testName}
                            onChange={(e) => handleResultChange(index, 'testName', e.target.value)}
                            placeholder="검사 항목명"
                          />
                        ) : (
                          result.testName
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
                              handleResultChange(index, 'flag', e.target.value as LabResultItem['flag'])
                            }
                          >
                            <option value="normal">정상</option>
                            <option value="abnormal">이상</option>
                            <option value="critical">Critical</option>
                          </select>
                        ) : (
                          getFlagDisplay(result.flag)
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
        )}

        {/* 해석/소견 탭 */}
        {activeTab === 'interpretation' && (
          <div className="interpretation-tab">
            <div className="form-group">
              <label>의학적 해석 (Interpretation)</label>
              {canEdit ? (
                <textarea
                  value={interpretation}
                  onChange={(e) => setInterpretation(e.target.value)}
                  placeholder="검사 결과에 대한 의학적 해석을 입력하세요..."
                  rows={6}
                />
              ) : (
                <div className="readonly-text">{interpretation || '해석 내용 없음'}</div>
              )}
            </div>

            <div className="form-group">
              <label>추가 메모</label>
              {canEdit ? (
                <textarea
                  value={notes}
                  onChange={(e) => setNotes(e.target.value)}
                  placeholder="추가 메모 사항..."
                  rows={4}
                />
              ) : (
                <div className="readonly-text">{notes || '메모 없음'}</div>
              )}
            </div>

            {criticalCount > 0 && (
              <div className="critical-warning">
                <strong>⚠️ Critical 결과 안내</strong>
                <p>
                  {criticalCount}개의 Critical 결과가 있습니다. 담당 의사에게 즉시 통보하고 해석
                  내용을 필수로 입력해주세요.
                </p>
              </div>
            )}

            <div className="disclaimer">
              <p>
                ※ 본 결과는 진단을 보조하기 위한 참고 자료이며 최종 판단은 의료진의 결정에 따릅니다.
              </p>
            </div>
          </div>
        )}

        {/* 이력 탭 */}
        {activeTab === 'history' && (
          <div className="history-tab">
            <table className="history-table">
              <thead>
                <tr>
                  <th>일시</th>
                  <th>액션</th>
                  <th>수행자</th>
                  <th>상태 변경</th>
                  <th>사유</th>
                </tr>
              </thead>
              <tbody>
                {ocs.history.map((h) => (
                  <tr key={h.id}>
                    <td>{formatDate(h.created_at)}</td>
                    <td>{h.action_display}</td>
                    <td>{h.actor?.name || '-'}</td>
                    <td>
                      {h.from_status && h.to_status
                        ? `${h.from_status} → ${h.to_status}`
                        : h.to_status || '-'}
                    </td>
                    <td>{h.reason || '-'}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </section>
    </div>
  );
}

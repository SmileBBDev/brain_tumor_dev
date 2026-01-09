/**
 * LIS 검사 결과 업로드 화면 (P.85)
 * - 외부 LIS/검사 장비에서 수신된 Raw 검사 결과 파일 업로드
 * - CSV/HL7/FHIR 형식 지원
 * - 파싱/정규화 처리 로그
 */
import { useState, useCallback, useRef } from 'react';
import './LISUploadPage.css';

// 업로드 상태 타입
type UploadStatus = 'idle' | 'uploading' | 'parsing' | 'success' | 'error';

// 업로드 로그 아이템
interface UploadLogItem {
  id: string;
  timestamp: string;
  fileName: string;
  fileSize: number;
  status: 'success' | 'error' | 'warning';
  message: string;
  recordCount?: number;
}

// 파일 크기 포맷
const formatFileSize = (bytes: number): string => {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
};

// 지원 파일 형식
const SUPPORTED_FORMATS = ['.csv', '.hl7', '.json', '.xml'];
const MAX_FILE_SIZE = 10 * 1024 * 1024; // 10MB

export default function LISUploadPage() {
  // 상태
  const [uploadStatus, setUploadStatus] = useState<UploadStatus>('idle');
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [uploadLogs, setUploadLogs] = useState<UploadLogItem[]>([]);
  const [dragActive, setDragActive] = useState(false);
  const [progressPercent, setProgressPercent] = useState(0);
  const fileInputRef = useRef<HTMLInputElement>(null);

  // 파일 선택 핸들러
  const handleFileSelect = useCallback((file: File) => {
    // 파일 형식 검증
    const extension = '.' + file.name.split('.').pop()?.toLowerCase();
    if (!SUPPORTED_FORMATS.includes(extension)) {
      addLog(file.name, file.size, 'error', `지원하지 않는 파일 형식입니다. (지원: ${SUPPORTED_FORMATS.join(', ')})`);
      return;
    }

    // 파일 크기 검증
    if (file.size > MAX_FILE_SIZE) {
      addLog(file.name, file.size, 'error', `파일 크기가 너무 큽니다. (최대: ${formatFileSize(MAX_FILE_SIZE)})`);
      return;
    }

    setSelectedFile(file);
    setUploadStatus('idle');
  }, []);

  // 드래그 핸들러
  const handleDrag = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === 'dragenter' || e.type === 'dragover') {
      setDragActive(true);
    } else if (e.type === 'dragleave') {
      setDragActive(false);
    }
  }, []);

  // 드롭 핸들러
  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);

    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      handleFileSelect(e.dataTransfer.files[0]);
    }
  }, [handleFileSelect]);

  // 파일 input 변경 핸들러
  const handleFileInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      handleFileSelect(e.target.files[0]);
    }
  };

  // 로그 추가
  const addLog = (fileName: string, fileSize: number, status: 'success' | 'error' | 'warning', message: string, recordCount?: number) => {
    const log: UploadLogItem = {
      id: `${Date.now()}-${Math.random().toString(36).substr(2, 9)}`,
      timestamp: new Date().toISOString(),
      fileName,
      fileSize,
      status,
      message,
      recordCount,
    };
    setUploadLogs((prev) => [log, ...prev].slice(0, 50));
  };

  // 업로드 시뮬레이션 (실제 구현 시 API 호출로 대체)
  const handleUpload = async () => {
    if (!selectedFile) return;

    setUploadStatus('uploading');
    setProgressPercent(0);

    try {
      // 업로드 진행 시뮬레이션
      for (let i = 0; i <= 50; i += 10) {
        await new Promise((resolve) => setTimeout(resolve, 100));
        setProgressPercent(i);
      }

      setUploadStatus('parsing');
      setProgressPercent(60);

      // 파싱 시뮬레이션
      await new Promise((resolve) => setTimeout(resolve, 500));
      setProgressPercent(80);

      // 저장 시뮬레이션
      await new Promise((resolve) => setTimeout(resolve, 300));
      setProgressPercent(100);

      // 성공
      setUploadStatus('success');
      const mockRecordCount = Math.floor(Math.random() * 50) + 10;
      addLog(selectedFile.name, selectedFile.size, 'success', `파일 처리 완료. ${mockRecordCount}개 레코드 저장됨.`, mockRecordCount);

      // 파일 초기화
      setSelectedFile(null);
      if (fileInputRef.current) {
        fileInputRef.current.value = '';
      }
    } catch (error) {
      setUploadStatus('error');
      addLog(selectedFile.name, selectedFile.size, 'error', '파일 처리 중 오류가 발생했습니다.');
    }
  };

  // 파일 취소
  const handleCancel = () => {
    setSelectedFile(null);
    setUploadStatus('idle');
    setProgressPercent(0);
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  };

  // 로그 시간 포맷
  const formatLogTime = (timestamp: string): string => {
    return new Date(timestamp).toLocaleString('ko-KR', {
      month: '2-digit',
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit',
    });
  };

  return (
    <div className="page lis-upload-page">
      {/* 헤더 */}
      <header className="page-header">
        <h2>검사 결과 업로드</h2>
        <span className="subtitle">외부 LIS/검사 장비의 Raw 데이터를 업로드합니다</span>
      </header>

      {/* 업로드 영역 */}
      <section className="upload-section">
        <div
          className={`upload-dropzone ${dragActive ? 'drag-active' : ''} ${selectedFile ? 'has-file' : ''}`}
          onDragEnter={handleDrag}
          onDragLeave={handleDrag}
          onDragOver={handleDrag}
          onDrop={handleDrop}
          onClick={() => fileInputRef.current?.click()}
        >
          <input
            ref={fileInputRef}
            type="file"
            accept={SUPPORTED_FORMATS.join(',')}
            onChange={handleFileInputChange}
            style={{ display: 'none' }}
          />

          {!selectedFile ? (
            <>
              <div className="upload-icon">📁</div>
              <p className="upload-text">
                파일을 드래그하거나 클릭하여 선택하세요
              </p>
              <p className="upload-hint">
                지원 형식: {SUPPORTED_FORMATS.join(', ')} (최대 {formatFileSize(MAX_FILE_SIZE)})
              </p>
            </>
          ) : (
            <>
              <div className="file-info">
                <span className="file-icon">📄</span>
                <div className="file-details">
                  <span className="file-name">{selectedFile.name}</span>
                  <span className="file-size">{formatFileSize(selectedFile.size)}</span>
                </div>
              </div>

              {uploadStatus !== 'idle' && (
                <div className="upload-progress">
                  <div className="progress-bar">
                    <div
                      className="progress-fill"
                      style={{ width: `${progressPercent}%` }}
                    />
                  </div>
                  <span className="progress-text">
                    {uploadStatus === 'uploading' && '업로드 중...'}
                    {uploadStatus === 'parsing' && '파싱/정규화 중...'}
                    {uploadStatus === 'success' && '완료!'}
                    {uploadStatus === 'error' && '오류 발생'}
                  </span>
                </div>
              )}
            </>
          )}
        </div>

        {selectedFile && uploadStatus === 'idle' && (
          <div className="upload-actions">
            <button className="upload-btn" onClick={handleUpload}>
              업로드 시작
            </button>
            <button className="cancel-btn" onClick={handleCancel}>
              취소
            </button>
          </div>
        )}

        {uploadStatus === 'success' && (
          <div className="upload-actions">
            <button className="upload-btn" onClick={() => fileInputRef.current?.click()}>
              다른 파일 업로드
            </button>
          </div>
        )}
      </section>

      {/* 처리 로그 */}
      <section className="log-section">
        <h3>처리 로그</h3>
        {uploadLogs.length === 0 ? (
          <div className="empty-log">아직 업로드 기록이 없습니다.</div>
        ) : (
          <table className="log-table">
            <thead>
              <tr>
                <th>시간</th>
                <th>파일명</th>
                <th>크기</th>
                <th>상태</th>
                <th>메시지</th>
              </tr>
            </thead>
            <tbody>
              {uploadLogs.map((log) => (
                <tr key={log.id} className={`log-row ${log.status}`}>
                  <td className="log-time">{formatLogTime(log.timestamp)}</td>
                  <td className="log-filename">{log.fileName}</td>
                  <td className="log-size">{formatFileSize(log.fileSize)}</td>
                  <td>
                    <span className={`status-badge ${log.status}`}>
                      {log.status === 'success' && '성공'}
                      {log.status === 'error' && '실패'}
                      {log.status === 'warning' && '경고'}
                    </span>
                  </td>
                  <td className="log-message">{log.message}</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </section>

      {/* 업로드 가이드 */}
      <section className="guide-section">
        <h3>업로드 가이드</h3>
        <div className="guide-content">
          <div className="guide-item">
            <h4>CSV 형식</h4>
            <p>첫 번째 행은 헤더여야 합니다. 필수 컬럼: patient_id, test_code, test_name, value, unit, reference</p>
          </div>
          <div className="guide-item">
            <h4>HL7 형식</h4>
            <p>HL7 v2.x 형식의 ORU 메시지를 지원합니다.</p>
          </div>
          <div className="guide-item">
            <h4>JSON/XML 형식</h4>
            <p>FHIR DiagnosticReport 리소스 형식을 지원합니다.</p>
          </div>
        </div>
      </section>
    </div>
  );
}

/**
 * LIS 검사 결과 업로드 화면 (P.85)
 * - 외부 LIS/검사 장비에서 수신된 Raw 검사 결과 파일 업로드
 * - CSV/HL7/FHIR 형식 지원
 * - 파싱/정규화 처리 로그
 */
import { useState, useCallback, useRef, useEffect } from 'react';
import {
  createExternalLIS,
  uploadLISFile,
  getOCSList,
  type CreateExternalLISRequest,
  type LISExternalSourceData,
} from '@/services/ocs.api';
import {
  createExternalPatient,
  type CreateExternalPatientRequest,
} from '@/services/patient.api';
import { api } from '@/services/api';
import type { OCSListItem } from '@/types/ocs';
import './LISUploadPage.css';

// 업로드 상태 타입
type UploadStatus = 'idle' | 'uploading' | 'parsing' | 'success' | 'error';

// 업로드 모드 타입
type UploadMode = 'new' | 'existing';

// 환자 선택 모드 타입 (새 외부 검사 등록 시)
type PatientMode = 'existing' | 'new';

// 업로드 로그 아이템
interface UploadLogItem {
  id: string;
  timestamp: string;
  fileName: string;
  fileSize: number;
  status: 'success' | 'error' | 'warning';
  message: string;
  ocsId?: string;
}

// 환자 정보 타입
interface PatientOption {
  id: number;
  name: string;
  patient_number: string;
}

// 외부 기관 정보 (선택적)
interface ExternalInstitutionInfo {
  institutionName: string;
  institutionCode: string;
  contactNumber: string;
  address: string;
}

// 검사 수행 정보 (선택적)
interface TestExecutionInfo {
  performedDate: string;
  performedBy: string;
  specimenCollectedDate: string;
  specimenType: string;
}

// 품질/인증 정보 (선택적)
interface QualityCertificationInfo {
  labCertificationNumber: string;
  qcStatus: string;
  isVerified: boolean;
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

// 검체 종류 옵션
const SPECIMEN_TYPES = [
  { value: '', label: '선택 안함' },
  { value: 'blood', label: '혈액' },
  { value: 'urine', label: '소변' },
  { value: 'csf', label: '뇌척수액' },
  { value: 'tissue', label: '조직' },
  { value: 'swab', label: '면봉 채취' },
  { value: 'other', label: '기타' },
];

// QC 상태 옵션
const QC_STATUS_OPTIONS = [
  { value: '', label: '선택 안함' },
  { value: 'passed', label: '통과' },
  { value: 'conditional', label: '조건부 통과' },
  { value: 'failed', label: '실패' },
  { value: 'pending', label: '검토 중' },
];

// 검사 종류 옵션
const JOB_TYPE_OPTIONS = [
  { value: 'BLOOD', label: '혈액 검사' },
  { value: 'GENETIC', label: '유전자 검사' },
  { value: 'PROTEIN', label: '단백질 검사' },
  { value: 'URINE', label: '소변 검사' },
  { value: 'CSF', label: '뇌척수액 검사' },
  { value: 'BIOPSY', label: '조직 검사' },
  { value: 'EXTERNAL', label: '기타' },
];

export default function LISUploadPage() {
  // 업로드 모드
  const [uploadMode, setUploadMode] = useState<UploadMode>('new');

  // 상태
  const [uploadStatus, setUploadStatus] = useState<UploadStatus>('idle');
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [uploadLogs, setUploadLogs] = useState<UploadLogItem[]>([]);
  const [dragActive, setDragActive] = useState(false);
  const [progressPercent, setProgressPercent] = useState(0);
  const fileInputRef = useRef<HTMLInputElement>(null);

  // 새 외부 검사 등록 모드 - 환자 선택/생성 (기본값: 새 환자 등록)
  const [patientMode, setPatientMode] = useState<PatientMode>('new');
  const [patients, setPatients] = useState<PatientOption[]>([]);
  const [selectedPatientId, setSelectedPatientId] = useState<number | null>(null);
  const [patientSearch, setPatientSearch] = useState('');
  const [isLoadingPatients, setIsLoadingPatients] = useState(false);

  // 새 환자 정보 (환자 생성 모드)
  const [newPatientName, setNewPatientName] = useState('');
  const [newPatientBirthDate, setNewPatientBirthDate] = useState('');
  const [newPatientGender, setNewPatientGender] = useState<'M' | 'F' | 'O'>('M');
  const [newPatientPhone, setNewPatientPhone] = useState('');
  const [isCreatingPatient, setIsCreatingPatient] = useState(false);

  // 새 외부 검사 등록 모드 - 검사 종류
  const [jobType, setJobType] = useState('BLOOD');

  // 기존 OCS 선택 모드
  const [lisOrders, setLisOrders] = useState<OCSListItem[]>([]);
  const [selectedOcsId, setSelectedOcsId] = useState<number | null>(null);
  const [selectedOcs, setSelectedOcs] = useState<OCSListItem | null>(null);
  const [ocsSearch, setOcsSearch] = useState('');
  const [isLoadingOcs, setIsLoadingOcs] = useState(false);

  // 추가 정보 섹션 토글
  const [showAdditionalInfo, setShowAdditionalInfo] = useState(false);

  // 외부 기관 정보 (선택적)
  const [institutionInfo, setInstitutionInfo] = useState<ExternalInstitutionInfo>({
    institutionName: '',
    institutionCode: '',
    contactNumber: '',
    address: '',
  });

  // 검사 수행 정보 (선택적)
  const [executionInfo, setExecutionInfo] = useState<TestExecutionInfo>({
    performedDate: '',
    performedBy: '',
    specimenCollectedDate: '',
    specimenType: '',
  });

  // 품질/인증 정보 (선택적)
  const [qualityInfo, setQualityInfo] = useState<QualityCertificationInfo>({
    labCertificationNumber: '',
    qcStatus: '',
    isVerified: false,
  });

  // 환자 목록 로드
  useEffect(() => {
    const loadPatients = async () => {
      setIsLoadingPatients(true);
      try {
        const response = await api.get<{ results: PatientOption[] }>('/patients/', {
          params: { page_size: 100 }
        });
        setPatients(response.data.results || []);
      } catch (error) {
        console.error('환자 목록 로드 실패:', error);
      } finally {
        setIsLoadingPatients(false);
      }
    };
    loadPatients();
  }, []);

  // LIS OCS 목록 로드
  useEffect(() => {
    const loadLisOrders = async () => {
      setIsLoadingOcs(true);
      try {
        const response = await getOCSList({ job_role: 'LIS', page_size: 100 });
        setLisOrders(response.results || []);
      } catch (error) {
        console.error('LIS 오더 목록 로드 실패:', error);
      } finally {
        setIsLoadingOcs(false);
      }
    };
    loadLisOrders();
  }, []);

  // 필터된 환자 목록
  const filteredPatients = patients.filter(p =>
    p.name.toLowerCase().includes(patientSearch.toLowerCase()) ||
    p.patient_number.toLowerCase().includes(patientSearch.toLowerCase())
  );

  // 필터된 OCS 목록
  const filteredOcs = lisOrders.filter(o =>
    o.ocs_id.toLowerCase().includes(ocsSearch.toLowerCase()) ||
    o.patient.name.toLowerCase().includes(ocsSearch.toLowerCase()) ||
    o.patient.patient_number.toLowerCase().includes(ocsSearch.toLowerCase())
  );

  // OCS 선택 시 기존 데이터 로드
  const handleOcsSelect = (ocsId: number | null) => {
    setSelectedOcsId(ocsId);

    if (ocsId) {
      const ocs = lisOrders.find(o => o.id === ocsId);
      setSelectedOcs(ocs || null);

      // 기존 외부 기관 정보가 있으면 폼에 채우기
      if (ocs) {
        const attachments = (ocs as any).attachments;
        if (attachments?.external_source) {
          const { institution, execution, quality } = attachments.external_source;

          if (institution) {
            setInstitutionInfo({
              institutionName: institution.name || '',
              institutionCode: institution.code || '',
              contactNumber: institution.contact || '',
              address: institution.address || '',
            });
          }

          if (execution) {
            setExecutionInfo({
              performedDate: execution.performed_date || '',
              performedBy: execution.performed_by || '',
              specimenCollectedDate: execution.specimen_collected_date || '',
              specimenType: execution.specimen_type || '',
            });
          }

          if (quality) {
            setQualityInfo({
              labCertificationNumber: quality.lab_certification_number || '',
              qcStatus: quality.qc_status || '',
              isVerified: quality.is_verified || false,
            });
          }

          // 기존 데이터가 있으면 추가 정보 섹션 열기
          if (institution?.name || execution?.performed_date || quality?.lab_certification_number) {
            setShowAdditionalInfo(true);
          }
        }
      }
    } else {
      setSelectedOcs(null);
    }
  };

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
  const addLog = (fileName: string, fileSize: number, status: 'success' | 'error' | 'warning', message: string, ocsId?: string) => {
    const log: UploadLogItem = {
      id: `${Date.now()}-${Math.random().toString(36).substr(2, 9)}`,
      timestamp: new Date().toISOString(),
      fileName,
      fileSize,
      status,
      message,
      ocsId,
    };
    setUploadLogs((prev) => [log, ...prev].slice(0, 50));
  };

  // 외부 기관 정보 구성
  const buildExternalData = (): LISExternalSourceData => ({
    institution_name: institutionInfo.institutionName || undefined,
    institution_code: institutionInfo.institutionCode || undefined,
    institution_contact: institutionInfo.contactNumber || undefined,
    institution_address: institutionInfo.address || undefined,
    performed_date: executionInfo.performedDate || undefined,
    performed_by: executionInfo.performedBy || undefined,
    specimen_collected_date: executionInfo.specimenCollectedDate || undefined,
    specimen_type: executionInfo.specimenType || undefined,
    lab_certification_number: qualityInfo.labCertificationNumber || undefined,
    qc_status: qualityInfo.qcStatus || undefined,
    is_verified: qualityInfo.isVerified ? 'true' : 'false',
  });

  // 실제 업로드/등록
  const handleUpload = async () => {
    // 모드별 검증
    if (uploadMode === 'new') {
      if (patientMode === 'existing' && !selectedPatientId) {
        addLog('등록', 0, 'error', '환자를 선택해주세요.');
        return;
      }
      if (patientMode === 'new' && (!newPatientName || !newPatientBirthDate)) {
        addLog('등록', 0, 'error', '환자 이름과 생년월일을 입력해주세요.');
        return;
      }
    }

    if (uploadMode === 'existing' && !selectedOcsId) {
      addLog('등록', 0, 'error', 'OCS를 선택해주세요.');
      return;
    }

    // 기존 OCS 모드에서 파일이 없으면 에러
    if (uploadMode === 'existing' && !selectedFile) {
      addLog('등록', 0, 'error', '업로드할 파일을 선택해주세요.');
      return;
    }

    setUploadStatus('uploading');
    setProgressPercent(0);

    const fileName = selectedFile?.name || '등록';
    const fileSize = selectedFile?.size || 0;

    try {
      let patientId = selectedPatientId;

      // 새 환자 생성이 필요한 경우
      if (uploadMode === 'new' && patientMode === 'new') {
        setProgressPercent(10);
        setIsCreatingPatient(true);

        const patientData: CreateExternalPatientRequest = {
          name: newPatientName,
          birth_date: newPatientBirthDate,
          gender: newPatientGender,
          phone: newPatientPhone || undefined,
          institution_name: institutionInfo.institutionName || undefined,
        };

        const patientResponse = await createExternalPatient(patientData);
        patientId = patientResponse.patient.id;
        setIsCreatingPatient(false);

        // 생성된 환자 정보 로그
        addLog(
          fileName,
          fileSize,
          'success',
          `외부 환자 등록 완료: ${patientResponse.patient.patient_number} (${patientResponse.patient.name})`
        );
      }

      setProgressPercent(30);

      const externalData = buildExternalData();

      setProgressPercent(50);
      setUploadStatus('parsing');

      let response;
      let resultOcsId: string;

      if (uploadMode === 'new') {
        // 새 외부 검사 등록 (파일은 선택사항)
        const requestData: CreateExternalLISRequest = {
          patient_id: patientId!,
          job_type: jobType,
          ...externalData,
        };

        response = await createExternalLIS(selectedFile, requestData);
        resultOcsId = response.ocs_id;
      } else {
        // 기존 OCS에 파일 추가 (파일 필수)
        response = await uploadLISFile(selectedOcsId!, selectedFile!, externalData);
        resultOcsId = selectedOcs?.ocs_id || String(selectedOcsId);
      }

      setProgressPercent(100);
      setUploadStatus('success');

      // 성공 로그
      const message = uploadMode === 'new'
        ? `외부 검사 등록 완료 (${resultOcsId})${selectedFile ? ' - 파일 첨부됨' : ''}`
        : `파일 업로드 완료 (${resultOcsId})`;

      addLog(fileName, fileSize, 'success', message, resultOcsId);

      // 폼 초기화
      resetForm();

    } catch (error: any) {
      setUploadStatus('error');
      setIsCreatingPatient(false);
      const errorMessage = error.response?.data?.error || '처리 중 오류가 발생했습니다.';
      addLog(fileName, fileSize, 'error', errorMessage);

      // 3초 후 idle 상태로 복귀하여 다시 시도 가능하게 함
      setTimeout(() => {
        setUploadStatus('idle');
      }, 3000);
    }
  };

  // 폼 초기화
  const resetForm = () => {
    setSelectedFile(null);
    setUploadStatus('idle');
    setProgressPercent(0);
    // 새 환자 정보 초기화
    setNewPatientName('');
    setNewPatientBirthDate('');
    setNewPatientGender('M');
    setNewPatientPhone('');
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  };

  // 파일 취소
  const handleCancel = () => {
    resetForm();
  };

  // 모드 변경 시 초기화
  const handleModeChange = (mode: UploadMode) => {
    setUploadMode(mode);
    resetForm();
    setSelectedPatientId(null);
    setSelectedOcsId(null);
    setSelectedOcs(null);
    setPatientMode('new');  // 기본값: 새 환자 등록
    // 추가 정보는 유지
  };

  // 환자 모드 변경
  const handlePatientModeChange = (mode: PatientMode) => {
    setPatientMode(mode);
    setSelectedPatientId(null);
    setNewPatientName('');
    setNewPatientBirthDate('');
    setNewPatientGender('M');
    setNewPatientPhone('');
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

  // 업로드 버튼 활성화 조건 (파일 없이도 정보 입력 시 활성화)
  const isNewPatientValid = newPatientName && newPatientBirthDate;
  const isUploadEnabled = (
    (uploadMode === 'new' && (
      (patientMode === 'existing' && selectedPatientId) ||
      (patientMode === 'new' && isNewPatientValid)
    )) ||
    (uploadMode === 'existing' && selectedOcsId)
  );

  return (
    <div className="page lis-upload-page">
      {/* 헤더 */}
      <header className="page-header">
        <h2>검사 결과 업로드</h2>
        <span className="subtitle">외부 LIS/검사 장비의 Raw 데이터를 등록합니다</span>
      </header>

      {/* 모드 선택 */}
      <section className="mode-select-section">
        <h3>업로드 유형</h3>
        <div className="mode-options">
          <label className={`mode-option ${uploadMode === 'new' ? 'selected' : ''}`}>
            <input
              type="radio"
              name="uploadMode"
              value="new"
              checked={uploadMode === 'new'}
              onChange={() => handleModeChange('new')}
            />
            <div className="mode-content">
              <span className="mode-title">새 외부 검사 등록</span>
              <span className="mode-desc">외부 기관 검사 결과를 새로 등록합니다 (extr_XXXX)</span>
            </div>
          </label>
          <label className={`mode-option ${uploadMode === 'existing' ? 'selected' : ''}`}>
            <input
              type="radio"
              name="uploadMode"
              value="existing"
              checked={uploadMode === 'existing'}
              onChange={() => handleModeChange('existing')}
            />
            <div className="mode-content">
              <span className="mode-title">기존 OCS에 파일 추가</span>
              <span className="mode-desc">기존 LIS 오더에 파일을 추가합니다</span>
            </div>
          </label>
        </div>
      </section>

      {/* 선택 섹션 - 모드에 따라 다른 UI */}
      <section className="selection-section">
        {uploadMode === 'new' ? (
          <>
            <h3>환자 정보 <span className="required">*</span></h3>

            {/* 환자 모드 선택 */}
            <div className="patient-mode-options">
              <label className={`patient-mode-option ${patientMode === 'new' ? 'selected' : ''}`}>
                <input
                  type="radio"
                  name="patientMode"
                  value="new"
                  checked={patientMode === 'new'}
                  onChange={() => handlePatientModeChange('new')}
                />
                <span>새 환자 등록 (EXTR_XXXX)</span>
              </label>
              <label className={`patient-mode-option ${patientMode === 'existing' ? 'selected' : ''}`}>
                <input
                  type="radio"
                  name="patientMode"
                  value="existing"
                  checked={patientMode === 'existing'}
                  onChange={() => handlePatientModeChange('existing')}
                />
                <span>기존 환자 선택</span>
              </label>
            </div>

            {patientMode === 'new' ? (
              /* 새 환자 등록 폼 */
              <div className="new-patient-form">
                <div className="form-grid">
                  <div className="form-field">
                    <label>환자명 <span className="required">*</span></label>
                    <input
                      type="text"
                      placeholder="홍길동"
                      value={newPatientName}
                      onChange={(e) => setNewPatientName(e.target.value)}
                    />
                  </div>
                  <div className="form-field">
                    <label>생년월일 <span className="required">*</span></label>
                    <input
                      type="date"
                      value={newPatientBirthDate}
                      onChange={(e) => setNewPatientBirthDate(e.target.value)}
                    />
                  </div>
                  <div className="form-field">
                    <label>성별 <span className="required">*</span></label>
                    <select
                      value={newPatientGender}
                      onChange={(e) => setNewPatientGender(e.target.value as 'M' | 'F' | 'O')}
                    >
                      <option value="M">남성</option>
                      <option value="F">여성</option>
                      <option value="O">기타</option>
                    </select>
                  </div>
                  <div className="form-field">
                    <label>전화번호</label>
                    <input
                      type="tel"
                      placeholder="010-1234-5678"
                      value={newPatientPhone}
                      onChange={(e) => setNewPatientPhone(e.target.value)}
                    />
                  </div>
                </div>
                <p className="form-hint">
                  외부 환자는 EXTR_0001 형식의 환자번호가 자동 생성됩니다.
                </p>
              </div>
            ) : (
              /* 기존 환자 선택 */
              <div className="select-container">
                <input
                  type="text"
                  className="search-input"
                  placeholder="환자명 또는 환자번호로 검색..."
                  value={patientSearch}
                  onChange={(e) => setPatientSearch(e.target.value)}
                />
                <select
                  className="main-select"
                  value={selectedPatientId || ''}
                  onChange={(e) => setSelectedPatientId(e.target.value ? Number(e.target.value) : null)}
                >
                  <option value="">환자를 선택하세요</option>
                  {isLoadingPatients ? (
                    <option disabled>로딩 중...</option>
                  ) : (
                    filteredPatients.map((patient) => (
                      <option key={patient.id} value={patient.id}>
                        {patient.name} ({patient.patient_number})
                      </option>
                    ))
                  )}
                </select>
              </div>
            )}

            {/* 검사 종류 선택 */}
            <div className="job-type-container">
              <label>검사 종류</label>
              <select
                className="job-type-select"
                value={jobType}
                onChange={(e) => setJobType(e.target.value)}
              >
                {JOB_TYPE_OPTIONS.map((option) => (
                  <option key={option.value} value={option.value}>{option.label}</option>
                ))}
              </select>
            </div>
          </>
        ) : (
          <>
            <h3>OCS 선택 <span className="required">*</span></h3>
            <div className="select-container">
              <input
                type="text"
                className="search-input"
                placeholder="OCS ID, 환자명 또는 환자번호로 검색..."
                value={ocsSearch}
                onChange={(e) => setOcsSearch(e.target.value)}
              />
              <select
                className="main-select"
                value={selectedOcsId || ''}
                onChange={(e) => handleOcsSelect(e.target.value ? Number(e.target.value) : null)}
              >
                <option value="">OCS를 선택하세요</option>
                {isLoadingOcs ? (
                  <option disabled>로딩 중...</option>
                ) : (
                  filteredOcs.map((ocs) => (
                    <option key={ocs.id} value={ocs.id}>
                      {ocs.ocs_id} - {ocs.patient.name} ({ocs.patient.patient_number}) - {ocs.ocs_status_display}
                    </option>
                  ))
                )}
              </select>
            </div>

            {/* 선택된 OCS 정보 표시 */}
            {selectedOcs && (
              <div className="selected-ocs-info">
                <div className="info-row">
                  <span className="label">환자:</span>
                  <span className="value">{selectedOcs.patient.name} ({selectedOcs.patient.patient_number})</span>
                </div>
                <div className="info-row">
                  <span className="label">검사 종류:</span>
                  <span className="value">{selectedOcs.job_type}</span>
                </div>
                <div className="info-row">
                  <span className="label">상태:</span>
                  <span className="value">{selectedOcs.ocs_status_display}</span>
                </div>
                <div className="info-row">
                  <span className="label">의뢰의사:</span>
                  <span className="value">{selectedOcs.doctor.name}</span>
                </div>
              </div>
            )}
          </>
        )}
      </section>

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
                    {uploadStatus === 'parsing' && '처리 중...'}
                    {uploadStatus === 'success' && '완료!'}
                    {uploadStatus === 'error' && '오류 발생'}
                  </span>
                </div>
              )}
            </>
          )}
        </div>

        {/* 업로드 버튼 - 항상 표시 */}
        <div className="upload-actions">
          {uploadStatus === 'success' ? (
            <button className="upload-btn" onClick={() => fileInputRef.current?.click()}>
              다른 파일 업로드
            </button>
          ) : (
            <>
              <button
                className="upload-btn"
                onClick={handleUpload}
                disabled={!isUploadEnabled || uploadStatus !== 'idle'}
              >
                {uploadStatus === 'uploading' || uploadStatus === 'parsing' ? '처리 중...' : '업로드 시작'}
              </button>
              {selectedFile && (
                <button className="cancel-btn" onClick={handleCancel} disabled={uploadStatus !== 'idle'}>
                  취소
                </button>
              )}
            </>
          )}
        </div>
      </section>

      {/* 추가 정보 입력 (선택적) */}
      <section className="additional-info-section">
        <div
          className="section-header-toggle"
          onClick={() => setShowAdditionalInfo(!showAdditionalInfo)}
        >
          <h3>
            <span className="toggle-icon">{showAdditionalInfo ? '▼' : '▶'}</span>
            추가 정보 입력 (선택사항)
          </h3>
          <span className="toggle-hint">외부 기관 검사 결과인 경우 입력하세요</span>
        </div>

        {showAdditionalInfo && (
          <div className="additional-info-form">
            {/* 외부 기관 정보 */}
            <div className="info-group">
              <h4>외부 기관 정보</h4>
              <div className="form-grid">
                <div className="form-field">
                  <label>기관명</label>
                  <input
                    type="text"
                    placeholder="예: 서울대학교병원 진단검사의학과"
                    value={institutionInfo.institutionName}
                    onChange={(e) => setInstitutionInfo({ ...institutionInfo, institutionName: e.target.value })}
                  />
                </div>
                <div className="form-field">
                  <label>기관 코드</label>
                  <input
                    type="text"
                    placeholder="예: SNUH-LAB-001"
                    value={institutionInfo.institutionCode}
                    onChange={(e) => setInstitutionInfo({ ...institutionInfo, institutionCode: e.target.value })}
                  />
                </div>
                <div className="form-field">
                  <label>연락처</label>
                  <input
                    type="tel"
                    placeholder="예: 02-1234-5678"
                    value={institutionInfo.contactNumber}
                    onChange={(e) => setInstitutionInfo({ ...institutionInfo, contactNumber: e.target.value })}
                  />
                </div>
                <div className="form-field full-width">
                  <label>주소</label>
                  <input
                    type="text"
                    placeholder="예: 서울특별시 종로구 대학로 101"
                    value={institutionInfo.address}
                    onChange={(e) => setInstitutionInfo({ ...institutionInfo, address: e.target.value })}
                  />
                </div>
              </div>
            </div>

            {/* 검사 수행 정보 */}
            <div className="info-group">
              <h4>검사 수행 정보</h4>
              <div className="form-grid">
                <div className="form-field">
                  <label>검사 수행일</label>
                  <input
                    type="date"
                    value={executionInfo.performedDate}
                    onChange={(e) => setExecutionInfo({ ...executionInfo, performedDate: e.target.value })}
                  />
                </div>
                <div className="form-field">
                  <label>검사자명</label>
                  <input
                    type="text"
                    placeholder="예: 김철수"
                    value={executionInfo.performedBy}
                    onChange={(e) => setExecutionInfo({ ...executionInfo, performedBy: e.target.value })}
                  />
                </div>
                <div className="form-field">
                  <label>검체 채취일</label>
                  <input
                    type="date"
                    value={executionInfo.specimenCollectedDate}
                    onChange={(e) => setExecutionInfo({ ...executionInfo, specimenCollectedDate: e.target.value })}
                  />
                </div>
                <div className="form-field">
                  <label>검체 종류</label>
                  <select
                    value={executionInfo.specimenType}
                    onChange={(e) => setExecutionInfo({ ...executionInfo, specimenType: e.target.value })}
                  >
                    {SPECIMEN_TYPES.map((type) => (
                      <option key={type.value} value={type.value}>{type.label}</option>
                    ))}
                  </select>
                </div>
              </div>
            </div>

            {/* 품질/인증 정보 */}
            <div className="info-group">
              <h4>품질/인증 정보</h4>
              <div className="form-grid">
                <div className="form-field">
                  <label>검사실 인증번호</label>
                  <input
                    type="text"
                    placeholder="예: KOLAS-ML-123"
                    value={qualityInfo.labCertificationNumber}
                    onChange={(e) => setQualityInfo({ ...qualityInfo, labCertificationNumber: e.target.value })}
                  />
                </div>
                <div className="form-field">
                  <label>QC 상태</label>
                  <select
                    value={qualityInfo.qcStatus}
                    onChange={(e) => setQualityInfo({ ...qualityInfo, qcStatus: e.target.value })}
                  >
                    {QC_STATUS_OPTIONS.map((option) => (
                      <option key={option.value} value={option.value}>{option.label}</option>
                    ))}
                  </select>
                </div>
                <div className="form-field checkbox-field">
                  <label>
                    <input
                      type="checkbox"
                      checked={qualityInfo.isVerified}
                      onChange={(e) => setQualityInfo({ ...qualityInfo, isVerified: e.target.checked })}
                    />
                    <span>검증 완료</span>
                  </label>
                </div>
              </div>
            </div>
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

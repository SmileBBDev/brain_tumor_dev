/**
 * RIS 영상 결과 업로드 화면
 * - 외부 RIS/PACS에서 수신된 영상 결과 파일 업로드
 * - DICOM/JPEG/PNG/PDF 형식 지원
 * - 파싱/정규화 처리 로그
 */
import { useState, useCallback, useRef, useEffect } from 'react';
import {
  createExternalRIS,
  uploadRISFile,
  getOCSList,
  type CreateExternalRISRequest,
  type RISExternalSourceData,
} from '@/services/ocs.api';
import {
  createExternalPatient,
  type CreateExternalPatientRequest,
} from '@/services/patient.api';
import { api } from '@/services/api';
import type { OCSListItem } from '@/types/ocs';
import './RISUploadPage.css';

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

// 촬영 정보 (선택적)
interface ImagingExecutionInfo {
  performedDate: string;
  performedBy: string;
  modality: string;
  bodyPart: string;
}

// 품질/인증 정보 (선택적)
interface QualityCertificationInfo {
  equipmentCertificationNumber: string;
  qcStatus: string;
  isVerified: boolean;
}

// 파일 크기 포맷
const formatFileSize = (bytes: number): string => {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
};

// 지원 파일 형식 (RIS용)
const SUPPORTED_FORMATS = ['.dcm', '.dicom', '.jpg', '.jpeg', '.png', '.pdf', '.zip'];
const MAX_FILE_SIZE = 100 * 1024 * 1024; // 100MB (영상 파일은 큼)

// 촬영 장비(Modality) 옵션
const MODALITY_OPTIONS = [
  { value: '', label: '선택 안함' },
  { value: 'CT', label: 'CT (컴퓨터 단층 촬영)' },
  { value: 'MR', label: 'MRI (자기공명영상)' },
  { value: 'CR', label: 'CR (컴퓨터 방사선)' },
  { value: 'DX', label: 'DX (디지털 X선)' },
  { value: 'US', label: 'US (초음파)' },
  { value: 'NM', label: 'NM (핵의학)' },
  { value: 'PT', label: 'PET (양전자 방출 단층 촬영)' },
  { value: 'MG', label: 'MG (유방 촬영)' },
  { value: 'XA', label: 'XA (혈관 조영)' },
  { value: 'OTHER', label: '기타' },
];

// 촬영 부위 옵션
const BODY_PART_OPTIONS = [
  { value: '', label: '선택 안함' },
  { value: 'HEAD', label: '두부 (Head)' },
  { value: 'BRAIN', label: '뇌 (Brain)' },
  { value: 'NECK', label: '경부 (Neck)' },
  { value: 'CHEST', label: '흉부 (Chest)' },
  { value: 'ABDOMEN', label: '복부 (Abdomen)' },
  { value: 'PELVIS', label: '골반 (Pelvis)' },
  { value: 'SPINE', label: '척추 (Spine)' },
  { value: 'EXTREMITY', label: '사지 (Extremity)' },
  { value: 'WHOLE_BODY', label: '전신 (Whole Body)' },
  { value: 'OTHER', label: '기타' },
];

// QC 상태 옵션
const QC_STATUS_OPTIONS = [
  { value: '', label: '선택 안함' },
  { value: 'passed', label: '통과' },
  { value: 'conditional', label: '조건부 통과' },
  { value: 'failed', label: '실패' },
  { value: 'pending', label: '검토 중' },
];

// 검사 종류 옵션 (RIS용)
const JOB_TYPE_OPTIONS = [
  { value: 'CT', label: 'CT 검사' },
  { value: 'MRI', label: 'MRI 검사' },
  { value: 'XRAY', label: 'X-ray 검사' },
  { value: 'ULTRASOUND', label: '초음파 검사' },
  { value: 'PET', label: 'PET 검사' },
  { value: 'ANGIO', label: '혈관조영 검사' },
  { value: 'EXTERNAL', label: '기타' },
];

export default function RISUploadPage() {
  // 업로드 모드
  const [uploadMode, setUploadMode] = useState<UploadMode>('new');

  // 상태
  const [uploadStatus, setUploadStatus] = useState<UploadStatus>('idle');
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [uploadLogs, setUploadLogs] = useState<UploadLogItem[]>([]);
  const [dragActive, setDragActive] = useState(false);
  const [progressPercent, setProgressPercent] = useState(0);
  const fileInputRef = useRef<HTMLInputElement>(null);

  // 새 외부 검사 등록 모드 - 환자 선택/생성
  // 기본값: 새 환자 등록
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
  const [_isCreatingPatient, setIsCreatingPatient] = useState(false);

  // 새 외부 검사 등록 모드 - 검사 종류
  const [jobType, setJobType] = useState('CT');

  // 기존 OCS 선택 모드
  const [risOrders, setRisOrders] = useState<OCSListItem[]>([]);
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

  // 촬영 수행 정보 (선택적)
  const [executionInfo, setExecutionInfo] = useState<ImagingExecutionInfo>({
    performedDate: '',
    performedBy: '',
    modality: '',
    bodyPart: '',
  });

  // 품질/인증 정보 (선택적)
  const [qualityInfo, setQualityInfo] = useState<QualityCertificationInfo>({
    equipmentCertificationNumber: '',
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

  // RIS OCS 목록 로드
  useEffect(() => {
    const loadRisOrders = async () => {
      setIsLoadingOcs(true);
      try {
        const response = await getOCSList({ job_role: 'RIS', page_size: 100 });
        setRisOrders(response.results || []);
      } catch (error) {
        console.error('RIS 오더 목록 로드 실패:', error);
      } finally {
        setIsLoadingOcs(false);
      }
    };
    loadRisOrders();
  }, []);

  // 필터된 환자 목록
  const filteredPatients = patients.filter(p =>
    p.name.toLowerCase().includes(patientSearch.toLowerCase()) ||
    p.patient_number.toLowerCase().includes(patientSearch.toLowerCase())
  );

  // 필터된 OCS 목록
  const filteredOcs = risOrders.filter(o =>
    o.ocs_id.toLowerCase().includes(ocsSearch.toLowerCase()) ||
    o.patient.name.toLowerCase().includes(ocsSearch.toLowerCase()) ||
    o.patient.patient_number.toLowerCase().includes(ocsSearch.toLowerCase())
  );

  // OCS 선택 시 기존 데이터 로드
  const handleOcsSelect = (ocsId: number | null) => {
    setSelectedOcsId(ocsId);

    if (ocsId) {
      const ocs = risOrders.find(o => o.id === ocsId);
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
              modality: execution.modality || '',
              bodyPart: execution.body_part || '',
            });
          }

          if (quality) {
            setQualityInfo({
              equipmentCertificationNumber: quality.equipment_certification_number || '',
              qcStatus: quality.qc_status || '',
              isVerified: quality.is_verified || false,
            });
          }

          // 기존 데이터가 있으면 추가 정보 섹션 열기
          if (institution?.name || execution?.performed_date || quality?.equipment_certification_number) {
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
  const buildExternalData = (): RISExternalSourceData => ({
    institution_name: institutionInfo.institutionName || undefined,
    institution_code: institutionInfo.institutionCode || undefined,
    institution_contact: institutionInfo.contactNumber || undefined,
    institution_address: institutionInfo.address || undefined,
    performed_date: executionInfo.performedDate || undefined,
    performed_by: executionInfo.performedBy || undefined,
    modality: executionInfo.modality || undefined,
    body_part: executionInfo.bodyPart || undefined,
    equipment_certification_number: qualityInfo.equipmentCertificationNumber || undefined,
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
        // 새 외부 영상 등록 (파일은 선택사항)
        const requestData: CreateExternalRISRequest = {
          patient_id: patientId!,
          job_type: jobType,
          ...externalData,
        };

        response = await createExternalRIS(selectedFile, requestData);
        resultOcsId = response.ocs_id;
      } else {
        // 기존 OCS에 파일 추가 (파일 필수)
        response = await uploadRISFile(selectedOcsId!, selectedFile!, externalData);
        resultOcsId = selectedOcs?.ocs_id || String(selectedOcsId);
      }

      setProgressPercent(100);
      setUploadStatus('success');

      // 성공 로그
      const message = uploadMode === 'new'
        ? `외부 영상 결과 등록 완료 (${resultOcsId})${selectedFile ? ' - 파일 첨부됨' : ''}`
        : `파일 업로드 완료 (${resultOcsId})`;

      addLog(fileName, fileSize, 'success', message, resultOcsId);

      // 폼 초기화
      resetForm();

    } catch (error: any) {
      setUploadStatus('error');
      setIsCreatingPatient(false);
      const errorMessage = error.response?.data?.error || '파일 처리 중 오류가 발생했습니다.';
      const fileName = selectedFile?.name || '등록';
      const fileSize = selectedFile?.size || 0;
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
    <div className="page ris-upload-page">
      {/* 헤더 */}
      <header className="page-header">
        {/* <h2>영상 결과 업로드</h2> */}
        <span className="subtitle">외부 RIS/PACS의 영상 데이터를 등록합니다</span>
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
              <span className="mode-title">새 외부 영상 등록</span>
              <span className="mode-desc">외부 기관 영상 결과를 새로 등록합니다 (risx_XXXX)</span>
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
              <span className="mode-desc">기존 RIS 오더에 파일을 추가합니다</span>
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
              <div className="upload-icon">🖼️</div>
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
                <span className="file-icon">🖼️</span>
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
          <span className="toggle-hint">외부 기관 영상 결과인 경우 입력하세요</span>
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
                    placeholder="예: 서울대학교병원 영상의학과"
                    value={institutionInfo.institutionName}
                    onChange={(e) => setInstitutionInfo({ ...institutionInfo, institutionName: e.target.value })}
                  />
                </div>
                <div className="form-field">
                  <label>기관 코드</label>
                  <input
                    type="text"
                    placeholder="예: SNUH-RAD-001"
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

            {/* 촬영 수행 정보 */}
            <div className="info-group">
              <h4>촬영 수행 정보</h4>
              <div className="form-grid">
                <div className="form-field">
                  <label>촬영 수행일</label>
                  <input
                    type="date"
                    value={executionInfo.performedDate}
                    onChange={(e) => setExecutionInfo({ ...executionInfo, performedDate: e.target.value })}
                  />
                </div>
                <div className="form-field">
                  <label>촬영자명</label>
                  <input
                    type="text"
                    placeholder="예: 김철수"
                    value={executionInfo.performedBy}
                    onChange={(e) => setExecutionInfo({ ...executionInfo, performedBy: e.target.value })}
                  />
                </div>
                <div className="form-field">
                  <label>촬영 장비 (Modality)</label>
                  <select
                    value={executionInfo.modality}
                    onChange={(e) => setExecutionInfo({ ...executionInfo, modality: e.target.value })}
                  >
                    {MODALITY_OPTIONS.map((option) => (
                      <option key={option.value} value={option.value}>{option.label}</option>
                    ))}
                  </select>
                </div>
                <div className="form-field">
                  <label>촬영 부위</label>
                  <select
                    value={executionInfo.bodyPart}
                    onChange={(e) => setExecutionInfo({ ...executionInfo, bodyPart: e.target.value })}
                  >
                    {BODY_PART_OPTIONS.map((option) => (
                      <option key={option.value} value={option.value}>{option.label}</option>
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
                  <label>장비 인증번호</label>
                  <input
                    type="text"
                    placeholder="예: KFDA-RAD-123"
                    value={qualityInfo.equipmentCertificationNumber}
                    onChange={(e) => setQualityInfo({ ...qualityInfo, equipmentCertificationNumber: e.target.value })}
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
            <h4>DICOM 형식</h4>
            <p>표준 DICOM 파일(.dcm)을 지원합니다. 여러 파일은 ZIP으로 압축하여 업로드하세요.</p>
          </div>
          <div className="guide-item">
            <h4>이미지 형식</h4>
            <p>JPEG, PNG 형식의 영상 캡처 이미지를 지원합니다.</p>
          </div>
          <div className="guide-item">
            <h4>PDF 형식</h4>
            <p>영상 판독 보고서 PDF 파일을 지원합니다.</p>
          </div>
        </div>
      </section>
    </div>
  );
}

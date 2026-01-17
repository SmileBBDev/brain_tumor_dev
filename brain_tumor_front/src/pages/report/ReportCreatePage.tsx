/**
 * 최종 보고서 작성 페이지
 * - 환자 선택
 * - 보고서 정보 입력
 * - 저장 및 제출
 */
import { useState, useCallback, useEffect } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import {
  createFinalReport,
  type FinalReportCreateData,
  type FinalReportType,
} from '@/services/report.api';
import { searchPatients } from '@/services/patient.api';
import type { Patient } from '@/types/patient';
import { useToast } from '@/components/common';
import './ReportCreatePage.css';

// 보고서 유형 옵션
const REPORT_TYPE_OPTIONS: { value: FinalReportType; label: string }[] = [
  { value: 'INITIAL', label: '초진 보고서' },
  { value: 'FOLLOWUP', label: '경과 보고서' },
  { value: 'DISCHARGE', label: '퇴원 보고서' },
  { value: 'FINAL', label: '최종 보고서' },
];

export default function ReportCreatePage() {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const toast = useToast();

  // 폼 데이터
  const [formData, setFormData] = useState<FinalReportCreateData>({
    patient: 0,
    report_type: 'FINAL',
    primary_diagnosis: '',
    secondary_diagnoses: [],
    diagnosis_date: new Date().toISOString().split('T')[0],
    treatment_summary: '',
    treatment_plan: '',
    ai_analysis_summary: '',
    clinical_findings: '',
    doctor_opinion: '',
    recommendations: '',
    prognosis: '',
  });

  // 환자 검색
  const [patientSearch, setPatientSearch] = useState('');
  const [patientResults, setPatientResults] = useState<Patient[]>([]);
  const [selectedPatient, setSelectedPatient] = useState<Patient | null>(null);
  const [searchingPatient, setSearchingPatient] = useState(false);
  const [showPatientDropdown, setShowPatientDropdown] = useState(false);

  // 부 진단명 입력
  const [secondaryInput, setSecondaryInput] = useState('');

  // 제출 상태
  const [submitting, setSubmitting] = useState(false);

  // URL 파라미터에서 환자 ID 가져오기
  useEffect(() => {
    const patientId = searchParams.get('patient_id');
    if (patientId) {
      const id = parseInt(patientId, 10);
      if (!isNaN(id)) {
        searchPatients({ id }).then(patients => {
          if (patients.length > 0) {
            setSelectedPatient(patients[0]);
            setFormData(prev => ({ ...prev, patient: patients[0].id }));
          }
        });
      }
    }
  }, [searchParams]);

  // 환자 검색
  const handlePatientSearch = useCallback(async (query: string) => {
    setPatientSearch(query);
    if (query.length < 2) {
      setPatientResults([]);
      setShowPatientDropdown(false);
      return;
    }

    setSearchingPatient(true);
    try {
      const results = await searchPatients({ q: query });
      setPatientResults(results);
      setShowPatientDropdown(true);
    } catch (error) {
      console.error('Patient search failed:', error);
    } finally {
      setSearchingPatient(false);
    }
  }, []);

  // 환자 선택
  const handlePatientSelect = useCallback((patient: Patient) => {
    setSelectedPatient(patient);
    setFormData(prev => ({ ...prev, patient: patient.id }));
    setPatientSearch('');
    setShowPatientDropdown(false);
  }, []);

  // 환자 선택 해제
  const handlePatientClear = useCallback(() => {
    setSelectedPatient(null);
    setFormData(prev => ({ ...prev, patient: 0 }));
  }, []);

  // 입력 변경 핸들러
  const handleInputChange = useCallback((
    e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement>
  ) => {
    const { name, value } = e.target;
    setFormData(prev => ({ ...prev, [name]: value }));
  }, []);

  // 부 진단명 추가
  const handleAddSecondary = useCallback(() => {
    if (secondaryInput.trim()) {
      setFormData(prev => ({
        ...prev,
        secondary_diagnoses: [...(prev.secondary_diagnoses || []), secondaryInput.trim()],
      }));
      setSecondaryInput('');
    }
  }, [secondaryInput]);

  // 부 진단명 삭제
  const handleRemoveSecondary = useCallback((index: number) => {
    setFormData(prev => ({
      ...prev,
      secondary_diagnoses: prev.secondary_diagnoses?.filter((_, i) => i !== index),
    }));
  }, []);

  // 폼 유효성 검사
  const validateForm = (): boolean => {
    if (!formData.patient) {
      toast.error('환자를 선택해주세요.');
      return false;
    }
    if (!formData.primary_diagnosis.trim()) {
      toast.error('주 진단명을 입력해주세요.');
      return false;
    }
    if (!formData.diagnosis_date) {
      toast.error('진단일을 입력해주세요.');
      return false;
    }
    return true;
  };

  // 저장 (임시 저장)
  const handleSave = useCallback(async () => {
    if (!validateForm()) return;

    setSubmitting(true);
    try {
      const report = await createFinalReport(formData);
      toast.success('보고서가 저장되었습니다.');
      navigate(`/reports/${report.id}`);
    } catch (error: any) {
      toast.error(error.response?.data?.detail || '보고서 저장에 실패했습니다.');
    } finally {
      setSubmitting(false);
    }
  }, [formData, navigate, toast]);

  // 취소
  const handleCancel = useCallback(() => {
    if (confirm('작성 중인 내용이 저장되지 않습니다. 취소하시겠습니까?')) {
      navigate('/reports/list');
    }
  }, [navigate]);

  return (
    <div className="page report-create-page">
      {/* 헤더 */}
      <header className="page-header">
        <button className="btn btn-back" onClick={handleCancel}>
          &larr; 목록
        </button>
        <div className="header-content">
          <h2>새 보고서 작성</h2>
          <span className="subtitle">최종 진료 보고서를 작성합니다</span>
        </div>
        <div className="header-actions">
          <button className="btn btn-secondary" onClick={handleCancel} disabled={submitting}>
            취소
          </button>
          <button className="btn btn-primary" onClick={handleSave} disabled={submitting}>
            {submitting ? '저장 중...' : '저장'}
          </button>
        </div>
      </header>

      <div className="form-container">
        {/* 기본 정보 섹션 */}
        <section className="form-section">
          <h3>기본 정보</h3>

          {/* 환자 선택 */}
          <div className="form-group">
            <label className="required">환자</label>
            {selectedPatient ? (
              <div className="selected-patient">
                <div className="patient-info">
                  <span className="patient-name">{selectedPatient.name}</span>
                  <span className="patient-number">{selectedPatient.patient_number}</span>
                  <span className="patient-birth">{selectedPatient.birth_date}</span>
                </div>
                <button type="button" className="btn-clear" onClick={handlePatientClear}>
                  변경
                </button>
              </div>
            ) : (
              <div className="patient-search">
                <input
                  type="text"
                  placeholder="환자명 또는 환자번호로 검색"
                  value={patientSearch}
                  onChange={(e) => handlePatientSearch(e.target.value)}
                  onFocus={() => patientResults.length > 0 && setShowPatientDropdown(true)}
                  onBlur={() => setTimeout(() => setShowPatientDropdown(false), 200)}
                />
                {searchingPatient && <span className="searching">검색 중...</span>}
                {showPatientDropdown && patientResults.length > 0 && (
                  <ul className="patient-dropdown">
                    {patientResults.map(patient => (
                      <li key={patient.id} onClick={() => handlePatientSelect(patient)}>
                        <span className="name">{patient.name}</span>
                        <span className="number">{patient.patient_number}</span>
                        <span className="birth">{patient.birth_date}</span>
                      </li>
                    ))}
                  </ul>
                )}
              </div>
            )}
          </div>

          {/* 보고서 유형 */}
          <div className="form-group">
            <label>보고서 유형</label>
            <select name="report_type" value={formData.report_type} onChange={handleInputChange}>
              {REPORT_TYPE_OPTIONS.map(opt => (
                <option key={opt.value} value={opt.value}>{opt.label}</option>
              ))}
            </select>
          </div>

          {/* 진단일 */}
          <div className="form-group">
            <label className="required">진단일</label>
            <input
              type="date"
              name="diagnosis_date"
              value={formData.diagnosis_date}
              onChange={handleInputChange}
            />
          </div>
        </section>

        {/* 진단 정보 섹션 */}
        <section className="form-section">
          <h3>진단 정보</h3>

          {/* 주 진단명 */}
          <div className="form-group">
            <label className="required">주 진단명</label>
            <input
              type="text"
              name="primary_diagnosis"
              value={formData.primary_diagnosis}
              onChange={handleInputChange}
              placeholder="주 진단명을 입력하세요"
            />
          </div>

          {/* 부 진단명 */}
          <div className="form-group">
            <label>부 진단명</label>
            <div className="secondary-diagnoses">
              <div className="add-secondary">
                <input
                  type="text"
                  value={secondaryInput}
                  onChange={(e) => setSecondaryInput(e.target.value)}
                  placeholder="부 진단명 추가"
                  onKeyPress={(e) => e.key === 'Enter' && (e.preventDefault(), handleAddSecondary())}
                />
                <button type="button" className="btn btn-add" onClick={handleAddSecondary}>
                  추가
                </button>
              </div>
              {formData.secondary_diagnoses && formData.secondary_diagnoses.length > 0 && (
                <ul className="secondary-list">
                  {formData.secondary_diagnoses.map((diag, index) => (
                    <li key={index}>
                      <span>{diag}</span>
                      <button type="button" className="btn-remove" onClick={() => handleRemoveSecondary(index)}>
                        &times;
                      </button>
                    </li>
                  ))}
                </ul>
              )}
            </div>
          </div>

          {/* 임상 소견 */}
          <div className="form-group">
            <label>임상 소견</label>
            <textarea
              name="clinical_findings"
              value={formData.clinical_findings}
              onChange={handleInputChange}
              placeholder="임상 소견을 입력하세요"
              rows={4}
            />
          </div>
        </section>

        {/* 치료 정보 섹션 */}
        <section className="form-section">
          <h3>치료 정보</h3>

          {/* 치료 요약 */}
          <div className="form-group">
            <label>치료 요약</label>
            <textarea
              name="treatment_summary"
              value={formData.treatment_summary}
              onChange={handleInputChange}
              placeholder="시행된 치료 내역을 요약해주세요"
              rows={4}
            />
          </div>

          {/* 향후 치료 계획 */}
          <div className="form-group">
            <label>향후 치료 계획</label>
            <textarea
              name="treatment_plan"
              value={formData.treatment_plan}
              onChange={handleInputChange}
              placeholder="향후 치료 계획을 입력하세요"
              rows={4}
            />
          </div>
        </section>

        {/* AI 분석 및 의사 소견 섹션 */}
        <section className="form-section">
          <h3>AI 분석 및 의사 소견</h3>

          {/* AI 분석 요약 */}
          <div className="form-group">
            <label>AI 분석 요약</label>
            <textarea
              name="ai_analysis_summary"
              value={formData.ai_analysis_summary}
              onChange={handleInputChange}
              placeholder="AI 추론 결과를 요약해주세요"
              rows={4}
            />
          </div>

          {/* 의사 소견 */}
          <div className="form-group">
            <label>의사 소견</label>
            <textarea
              name="doctor_opinion"
              value={formData.doctor_opinion}
              onChange={handleInputChange}
              placeholder="의사 소견을 입력하세요"
              rows={4}
            />
          </div>

          {/* 권고 사항 */}
          <div className="form-group">
            <label>권고 사항</label>
            <textarea
              name="recommendations"
              value={formData.recommendations}
              onChange={handleInputChange}
              placeholder="환자에 대한 권고 사항을 입력하세요"
              rows={4}
            />
          </div>

          {/* 예후 */}
          <div className="form-group">
            <label>예후</label>
            <textarea
              name="prognosis"
              value={formData.prognosis}
              onChange={handleInputChange}
              placeholder="예상 경과를 입력하세요"
              rows={3}
            />
          </div>
        </section>

        {/* 하단 버튼 */}
        <div className="form-actions">
          <button className="btn btn-secondary" onClick={handleCancel} disabled={submitting}>
            취소
          </button>
          <button className="btn btn-primary" onClick={handleSave} disabled={submitting}>
            {submitting ? '저장 중...' : '저장'}
          </button>
        </div>
      </div>

      <toast.ToastContainer position="top-right" />
    </div>
  );
}

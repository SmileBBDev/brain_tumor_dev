/**
 * AI 추론 요청 생성 페이지
 * - 환자 선택
 * - 모델 선택 및 데이터 검증
 * - 추론 요청 생성
 */
import { useState, useCallback, useEffect } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { useAuth } from '../auth/AuthProvider';
import { usePatientAvailableModels, useCreateAIRequest } from '@/hooks';
import { LoadingSpinner, useToast } from '@/components/common';
import { searchPatients } from '@/services/patient.api';
import type { AvailableModel, DataValidationResult } from '@/services/ai.api';
import './AIRequestCreatePage.css';

interface Patient {
  id: number;
  patient_number: string;
  name: string;
  birth_date: string;
  gender: string;
}

export default function AIRequestCreatePage() {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const toast = useToast();

  // URL에서 환자 ID 추출 (환자 상세에서 바로 이동한 경우)
  const initialPatientId = searchParams.get('patientId');

  // 상태
  const [step, setStep] = useState<'patient' | 'model' | 'confirm'>('patient');
  const [searchQuery, setSearchQuery] = useState('');
  const [searchResults, setSearchResults] = useState<Patient[]>([]);
  const [searching, setSearching] = useState(false);
  const [selectedPatient, setSelectedPatient] = useState<Patient | null>(null);
  const [selectedModel, setSelectedModel] = useState<AvailableModel | null>(null);
  const [priority, setPriority] = useState<string>('normal');
  const [validationResult, setValidationResult] = useState<DataValidationResult | null>(null);

  // Hooks
  const { models, availableModels, unavailableModels, loading: modelsLoading } = usePatientAvailableModels(
    selectedPatient?.id ?? null
  );
  const { create, validate, creating, validating, error } = useCreateAIRequest();

  // 초기 환자 ID로 환자 정보 조회
  useEffect(() => {
    if (initialPatientId) {
      const fetchPatient = async () => {
        try {
          const results = await searchPatients({ id: Number(initialPatientId) });
          if (results.length > 0) {
            setSelectedPatient(results[0]);
            setStep('model');
          }
        } catch (err) {
          console.error('Failed to fetch patient:', err);
        }
      };
      fetchPatient();
    }
  }, [initialPatientId]);

  // 환자 검색
  const handleSearch = useCallback(async () => {
    if (!searchQuery.trim()) return;

    setSearching(true);
    try {
      const results = await searchPatients({ q: searchQuery });
      setSearchResults(results);
    } catch (err) {
      console.error('Failed to search patients:', err);
      toast.error('환자 검색에 실패했습니다.');
    } finally {
      setSearching(false);
    }
  }, [searchQuery, toast]);

  // 환자 선택
  const handleSelectPatient = useCallback((patient: Patient) => {
    setSelectedPatient(patient);
    setSelectedModel(null);
    setValidationResult(null);
    setStep('model');
  }, []);

  // 모델 선택
  const handleSelectModel = useCallback(
    async (model: AvailableModel) => {
      if (!model.is_available || !selectedPatient) return;

      setSelectedModel(model);

      // 데이터 검증 실행
      try {
        const result = await validate(selectedPatient.id, model.code);
        setValidationResult(result);

        if (result.valid) {
          setStep('confirm');
        } else {
          toast.warning('필요한 데이터가 부족합니다. 상세 내용을 확인해주세요.');
        }
      } catch (err) {
        toast.error('데이터 검증에 실패했습니다.');
      }
    },
    [selectedPatient, validate, toast]
  );

  // 요청 생성
  const handleCreate = useCallback(async () => {
    if (!selectedPatient || !selectedModel) return;

    try {
      const request = await create(selectedPatient.id, selectedModel.code, priority);
      toast.success('AI 분석 요청이 생성되었습니다.');
      navigate(`/ai/requests/${request.id}`);
    } catch (err) {
      toast.error('AI 분석 요청 생성에 실패했습니다.');
    }
  }, [selectedPatient, selectedModel, priority, create, navigate, toast]);

  // 뒤로 가기
  const handleBack = useCallback(() => {
    if (step === 'confirm') {
      setStep('model');
    } else if (step === 'model') {
      setStep('patient');
      setSelectedPatient(null);
      setSelectedModel(null);
      setValidationResult(null);
    } else {
      navigate(-1);
    }
  }, [step, navigate]);

  return (
    <div className="page ai-request-create">
      {/* 헤더 */}
      <header className="page-header">
        <button className="btn btn-back" onClick={handleBack}>
          &larr; 뒤로
        </button>
        <div className="header-content">
          <h2>새 AI 분석 요청</h2>
          <span className="subtitle">
            {step === 'patient' && '환자를 선택해주세요'}
            {step === 'model' && 'AI 모델을 선택해주세요'}
            {step === 'confirm' && '요청 내용을 확인해주세요'}
          </span>
        </div>
      </header>

      {/* 진행 단계 표시 */}
      <div className="step-indicator">
        <div className={`step ${step === 'patient' ? 'active' : selectedPatient ? 'completed' : ''}`}>
          <span className="step-number">1</span>
          <span className="step-label">환자 선택</span>
        </div>
        <div className="step-divider"></div>
        <div className={`step ${step === 'model' ? 'active' : selectedModel ? 'completed' : ''}`}>
          <span className="step-number">2</span>
          <span className="step-label">모델 선택</span>
        </div>
        <div className="step-divider"></div>
        <div className={`step ${step === 'confirm' ? 'active' : ''}`}>
          <span className="step-number">3</span>
          <span className="step-label">확인 및 요청</span>
        </div>
      </div>

      {/* Step 1: 환자 선택 */}
      {step === 'patient' && (
        <section className="step-content patient-selection">
          <div className="search-box">
            <input
              type="text"
              placeholder="환자명 또는 환자번호로 검색"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && handleSearch()}
            />
            <button className="btn btn-primary" onClick={handleSearch} disabled={searching}>
              {searching ? '검색 중...' : '검색'}
            </button>
          </div>

          {searching ? (
            <LoadingSpinner text="환자를 검색하는 중..." />
          ) : searchResults.length > 0 ? (
            <div className="patient-list">
              {searchResults.map((patient) => (
                <div
                  key={patient.id}
                  className="patient-card"
                  onClick={() => handleSelectPatient(patient)}
                >
                  <div className="patient-info">
                    <span className="patient-name">{patient.name}</span>
                    <span className="patient-number">{patient.patient_number}</span>
                  </div>
                  <div className="patient-details">
                    <span>{patient.birth_date}</span>
                    <span>{patient.gender === 'M' ? '남' : '여'}</span>
                  </div>
                </div>
              ))}
            </div>
          ) : searchQuery && !searching ? (
            <div className="empty-result">
              <p>검색 결과가 없습니다.</p>
            </div>
          ) : null}
        </section>
      )}

      {/* Step 2: 모델 선택 */}
      {step === 'model' && selectedPatient && (
        <section className="step-content model-selection">
          <div className="selected-patient-info">
            <span className="label">선택된 환자:</span>
            <span className="patient-name">{selectedPatient.name}</span>
            <span className="patient-number">({selectedPatient.patient_number})</span>
          </div>

          {modelsLoading ? (
            <LoadingSpinner text="사용 가능한 모델을 확인하는 중..." />
          ) : (
            <>
              {/* 사용 가능한 모델 */}
              <div className="model-section">
                <h3>사용 가능한 모델</h3>
                {availableModels.length > 0 ? (
                  <div className="model-list">
                    {availableModels.map((model) => (
                      <div
                        key={model.code}
                        className={`model-card available ${selectedModel?.code === model.code ? 'selected' : ''}`}
                        onClick={() => handleSelectModel(model)}
                      >
                        <div className="model-header">
                          <span className="model-name">{model.name}</span>
                          <span className="model-code">{model.code}</span>
                        </div>
                        <p className="model-description">{model.description}</p>
                        <div className="model-data">
                          <span className="available-keys">
                            사용 데이터: {model.available_keys.join(', ')}
                          </span>
                        </div>
                      </div>
                    ))}
                  </div>
                ) : (
                  <div className="empty-models">
                    <p>사용 가능한 모델이 없습니다.</p>
                    <p className="hint">필요한 검사 데이터가 충족되면 모델을 사용할 수 있습니다.</p>
                  </div>
                )}
              </div>

              {/* 데이터 부족 모델 */}
              {unavailableModels.length > 0 && (
                <div className="model-section unavailable">
                  <h3>데이터 부족 모델</h3>
                  <div className="model-list">
                    {unavailableModels.map((model) => (
                      <div key={model.code} className="model-card disabled">
                        <div className="model-header">
                          <span className="model-name">{model.name}</span>
                          <span className="model-code">{model.code}</span>
                        </div>
                        <p className="model-description">{model.description}</p>
                        <div className="model-data missing">
                          <span className="missing-keys">
                            필요 데이터: {model.missing_keys.join(', ')}
                          </span>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* 검증 결과 */}
              {validating && <LoadingSpinner text="데이터 검증 중..." />}

              {validationResult && !validationResult.valid && (
                <div className="validation-error">
                  <h4>데이터 검증 실패</h4>
                  <p>누락된 데이터: {validationResult.missing_keys.join(', ')}</p>
                </div>
              )}
            </>
          )}
        </section>
      )}

      {/* Step 3: 확인 및 요청 */}
      {step === 'confirm' && selectedPatient && selectedModel && validationResult?.valid && (
        <section className="step-content confirmation">
          <div className="confirmation-card">
            <h3>AI 분석 요청 확인</h3>

            <div className="info-group">
              <label>환자 정보</label>
              <div className="info-value">
                <span className="patient-name">{selectedPatient.name}</span>
                <span className="patient-number">{selectedPatient.patient_number}</span>
              </div>
            </div>

            <div className="info-group">
              <label>분석 모델</label>
              <div className="info-value">
                <span className="model-name">{selectedModel.name}</span>
                <span className="model-code">({selectedModel.code})</span>
              </div>
            </div>

            <div className="info-group">
              <label>사용 데이터</label>
              <div className="info-value">
                <ul className="data-list">
                  {validationResult.available_keys.map((key) => (
                    <li key={key}>{key}</li>
                  ))}
                </ul>
              </div>
            </div>

            <div className="info-group">
              <label>우선순위</label>
              <div className="priority-selector">
                {['low', 'normal', 'high', 'urgent'].map((p) => (
                  <button
                    key={p}
                    className={`priority-btn ${priority === p ? 'selected' : ''} priority-${p}`}
                    onClick={() => setPriority(p)}
                  >
                    {p === 'low' && '낮음'}
                    {p === 'normal' && '보통'}
                    {p === 'high' && '높음'}
                    {p === 'urgent' && '긴급'}
                  </button>
                ))}
              </div>
            </div>

            <div className="action-buttons">
              <button className="btn btn-secondary" onClick={handleBack}>
                이전
              </button>
              <button
                className="btn btn-primary"
                onClick={handleCreate}
                disabled={creating}
              >
                {creating ? '요청 중...' : 'AI 분석 요청'}
              </button>
            </div>

            {error && <div className="error-message">{error}</div>}
          </div>
        </section>
      )}

      <toast.ToastContainer position="top-right" />
    </div>
  );
}

/**
 * Clinic 진료 페이지 (스토리보드 48p 기반)
 * 3컬럼 그리드 레이아웃 - 환자 진료 화면
 */
import { useState, useEffect, useCallback } from 'react';
import { useSearchParams, useNavigate } from 'react-router-dom';
import { getPatient } from '@/services/patient.api';
import { getOCSByPatient } from '@/services/ocs.api';
import { getEncounters, createEncounter, completeEncounter } from '@/services/encounter.api';
import { LoadingSpinner, useToast } from '@/components/common';
import { useAuth } from '@/pages/auth/AuthProvider';
import ExaminationTab from './components/ExaminationTab';
import type { OCSListItem } from '@/types/ocs';
import type { Encounter } from '@/types/encounter';
import './ClinicPage.css';

interface Patient {
  id: number;
  patient_number: string;
  name: string;
  birth_date: string;
  gender: string;
  phone?: string;
}

export default function ClinicPage() {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const toast = useToast();
  const { role } = useAuth();

  // 의사 역할 확인 (진료 시작 가능 여부)
  const isDoctor = role === 'DOCTOR';

  // URL에서 환자 ID 추출
  const patientIdParam = searchParams.get('patientId');

  // /patientsCare → /patientsCare?patientId=null 로 리다이렉트
  useEffect(() => {
    if (patientIdParam === null) {
      navigate('/patientsCare?patientId=null', { replace: true });
    }
  }, [patientIdParam, navigate]);

  // patientId=null → 환자 미선택 상태
  const isPatientSelected = patientIdParam && patientIdParam !== 'null';

  // 환자 선택하지 않기 (OCS 등에서 돌아올 때 사용)
  const handleClearPatient = () => {
    navigate('/patientsCare?patientId=null');
  };

  // 상태
  const [patient, setPatient] = useState<Patient | null>(null);
  const [ocsList, setOcsList] = useState<OCSListItem[]>([]);
  const [encounters, setEncounters] = useState<Encounter[]>([]);
  const [loading, setLoading] = useState(true);
  const [activeEncounter, setActiveEncounter] = useState<Encounter | null>(null);

  // 환자 데이터 로드
  const loadPatientData = useCallback(async (patientId: number) => {
    setLoading(true);
    try {
      // 환자 정보 조회
      const patientData = await getPatient(patientId);
      setPatient(patientData);

      // OCS 목록 조회
      const ocsData = await getOCSByPatient(patientId);
      setOcsList(ocsData);

      // 진료 기록 조회
      const encounterData = await getEncounters({ patient: patientId });
      setEncounters(encounterData.results || []);

      // 오늘 진행 중인 진료 찾기
      const today = new Date().toISOString().split('T')[0];
      const todayEncounter = (encounterData.results || []).find(
        (e: Encounter) => {
          // admission_date에서 날짜 부분만 추출 (ISO 형식: 2024-01-01T10:00:00Z)
          const admissionDate = e.admission_date?.split('T')[0];
          return admissionDate === today && e.status === 'in_progress';
        }
      );
      setActiveEncounter(todayEncounter || null);
    } catch (err) {
      console.error('Failed to load patient data:', err);
      toast.error('환자 데이터를 불러오는데 실패했습니다.');
    } finally {
      setLoading(false);
    }
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);  // toast 제거 - 안정적인 참조

  useEffect(() => {
    if (isPatientSelected) {
      loadPatientData(Number(patientIdParam));
    } else {
      // 환자 미선택 - 상태 초기화
      setPatient(null);
      setOcsList([]);
      setEncounters([]);
      setActiveEncounter(null);
      setLoading(false);
    }
  }, [patientIdParam, isPatientSelected, loadPatientData]);

  // 진료 시작
  const handleStartEncounter = useCallback(async () => {
    if (!patient) return;

    try {
      const encounter = await createEncounter({
        patient: patient.id,
        encounter_type: 'outpatient',
        status: 'in_progress',
        // chief_complaint, attending_doctor, department, admission_date는 백엔드에서 자동 설정됨
      });
      setActiveEncounter(encounter);
      toast.success('진료가 시작되었습니다.');
      // 진료 목록 새로고침
      const encounterData = await getEncounters({ patient: patient.id });
      setEncounters(encounterData.results || []);
    } catch (err: any) {
      console.error('Failed to start encounter:', err);
      console.error('Error response:', err.response?.data);
      const errorMsg = err.response?.data?.attending_doctor?.[0]
        || err.response?.data?.patient?.[0]
        || err.response?.data?.detail
        || '진료 시작에 실패했습니다.';
      toast.error(errorMsg);
    }
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [patient]);

  // 진료 종료 (안전 저장)
  const handleEndEncounter = useCallback(async () => {
    if (!activeEncounter || !patient) return;

    try {
      await completeEncounter(activeEncounter.id);
      setActiveEncounter(null);
      toast.success('진료가 완료되었습니다.');
      // 진료 목록 새로고침
      const encounterData = await getEncounters({ patient: patient.id });
      setEncounters(encounterData.results || []);
    } catch (err: any) {
      console.error('Failed to end encounter:', err);
      const errorMsg = err.response?.data?.detail || '진료 종료에 실패했습니다.';
      toast.error(errorMsg);
    }
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [activeEncounter, patient]);

  // 나이 계산
  const calculateAge = (birthDate: string) => {
    const today = new Date();
    const birth = new Date(birthDate);
    let age = today.getFullYear() - birth.getFullYear();
    const m = today.getMonth() - birth.getMonth();
    if (m < 0 || (m === 0 && today.getDate() < birth.getDate())) {
      age--;
    }
    return age;
  };

  if (loading && isPatientSelected) {
    return (
      <div className="page clinic-page">
        <LoadingSpinner text="환자 정보를 불러오는 중..." />
      </div>
    );
  }

  // 환자 ID가 있는데 환자를 찾을 수 없는 경우 (잘못된 ID)
  if (isPatientSelected && !patient) {
    return (
      <div className="page clinic-page">
        <div className="no-patient">
          <h2>환자를 찾을 수 없습니다</h2>
          <button className="btn btn-primary" onClick={() => navigate('/patients')}>
            환자 목록으로 이동
          </button>
        </div>
      </div>
    );
  }

  // 환자 미선택 상태용 더미 데이터
  const displayPatient = patient || {
    id: 0,
    patient_number: '-',
    name: '환자 ID 조회필요',
    birth_date: '-',
    gender: '',
    phone: '',
  };

  return (
    <div className="page clinic-page">
      {/* 환자 정보 헤더 */}
      <header className="patient-header enhanced">
        <div className="patient-info">
          <div className={`patient-avatar ${!patient ? 'patient-avatar-empty' : ''}`}>
            {patient
              ? (patient.gender === 'M' ? '👨' : '👩')
              : '❓'}
          </div>
          <div className="patient-details">
            <div className="patient-name-row">
              <h1 className="patient-name">{displayPatient.name}</h1>
              {!patient && <span className="patient-status-badge">미선택</span>}
              {patient && activeEncounter && <span className="encounter-status-badge">진료 중</span>}
            </div>
            <div className="patient-meta">
              {patient ? (
                <>
                  <span className="patient-number">{patient.patient_number}</span>
                  <span className="divider">|</span>
                  <span>{patient.birth_date} ({calculateAge(patient.birth_date)}세)</span>
                  <span className="divider">|</span>
                  <span>{patient.gender === 'M' ? '남성' : '여성'}</span>
                  {patient.phone && (
                    <>
                      <span className="divider">|</span>
                      <span>{patient.phone}</span>
                    </>
                  )}
                </>
              ) : (
                <span>예약 목록에서 환자를 선택하거나 환자 목록에서 검색하세요.</span>
              )}
            </div>
          </div>
        </div>

        {/* 퀵 액션 및 요약 */}
        <div className="header-right">
          {patient && (
            <div className="quick-stats">
              <div className="stat-item">
                <span className="stat-label">진료 기록</span>
                <span className="stat-value">{encounters.length}회</span>
              </div>
              <div className="stat-item">
                <span className="stat-label">검사 오더</span>
                <span className="stat-value">{ocsList.length}건</span>
              </div>
            </div>
          )}
          <div className="header-actions">
            {patient && !activeEncounter && isDoctor && (
              <button className="btn btn-primary" onClick={handleStartEncounter}>
                진료 시작
              </button>
            )}
            {patient && activeEncounter && isDoctor && (
              <button className="btn btn-success" onClick={handleEndEncounter}>
                진료 종료
              </button>
            )}
            {patient && (
              <>
                <button
                  className="btn btn-secondary btn-icon-text"
                  onClick={() => navigate(`/patients/${patient.id}`)}
                  title="환자 상세 정보"
                >
                  <span>상세 보기</span>
                </button>
                <button
                  className="btn btn-outline"
                  onClick={handleClearPatient}
                  title="환자 선택하지 않기"
                >
                  환자 선택 해제
                </button>
              </>
            )}
          </div>
        </div>
      </header>

      {/* 진찰 컨텐츠 */}
      <div className="clinic-tab-content">
        <ExaminationTab
          patientId={patient?.id || 0}
          encounterId={activeEncounter?.id || null}
          encounter={activeEncounter}
          ocsList={ocsList}
          encounters={encounters}
          onUpdate={() => patient && loadPatientData(patient.id)}
        />
      </div>
    </div>
  );
}

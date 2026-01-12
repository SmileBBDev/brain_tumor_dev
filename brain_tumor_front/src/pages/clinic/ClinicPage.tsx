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
import TodaySymptomCard from './components/TodaySymptomCard';
import DiagnosisPrescriptionCard from './components/DiagnosisPrescriptionCard';
import OrderCard from './components/OrderCard';
import PastRecordCard from './components/PastRecordCard';
import CalendarCard from './components/CalendarCard';
import LabResultCard from './components/LabResultCard';
import TodayAppointmentCard from './components/TodayAppointmentCard';
import PastPrescriptionCard from './components/PastPrescriptionCard';
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
    if (patientIdParam) {
      loadPatientData(Number(patientIdParam));
    } else {
      setLoading(false);
    }
  }, [patientIdParam, loadPatientData]);

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

  // 환자 선택 안됨 - 금일 예약 목록 표시
  if (!patientIdParam) {
    return (
      <div className="page clinic-page">
        <header className="patient-header">
          <div className="patient-info">
            <div className="patient-avatar">📋</div>
            <div className="patient-details">
              <h1 className="patient-name">환자 진료</h1>
              <div className="patient-meta">
                <span>금일 예약된 환자를 선택하거나, 환자 목록에서 검색하세요.</span>
              </div>
            </div>
          </div>
          <div className="header-actions">
            <button className="btn btn-secondary" onClick={() => navigate('/patients')}>
              환자 목록
            </button>
          </div>
        </header>

        <div className="clinic-grid">
          <div className="clinic-column column-full">
            <TodayAppointmentCard />
          </div>
        </div>
      </div>
    );
  }

  if (loading) {
    return (
      <div className="page clinic-page">
        <LoadingSpinner text="환자 정보를 불러오는 중..." />
      </div>
    );
  }

  if (!patient) {
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

  // LIS 결과만 필터링
  const lisResults = ocsList.filter(ocs => ocs.job_role === 'LIS');

  return (
    <div className="page clinic-page">
      {/* 환자 정보 헤더 */}
      <header className="patient-header">
        <div className="patient-info">
          <div className="patient-avatar">
            {patient.gender === 'M' ? '👨' : '👩'}
          </div>
          <div className="patient-details">
            <h1 className="patient-name">{patient.name}</h1>
            <div className="patient-meta">
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
            </div>
          </div>
        </div>
        <div className="header-actions">
          {!activeEncounter && isDoctor && (
            <button className="btn btn-primary" onClick={handleStartEncounter}>
              진료 시작
            </button>
          )}
          {activeEncounter && isDoctor && (
            <>
              <span className="encounter-badge active">진료 중</span>
              <button className="btn btn-success" onClick={handleEndEncounter}>
                진료 종료
              </button>
            </>
          )}
        </div>
      </header>

      {/* 3컬럼 그리드 레이아웃 */}
      <div className="clinic-grid">
        {/* 컬럼 1: 진료 입력 */}
        <div className="clinic-column column-1">
          <TodaySymptomCard
            patientId={patient.id}
            encounter={activeEncounter}
            onUpdate={() => loadPatientData(patient.id)}
          />
          <DiagnosisPrescriptionCard
            patientId={patient.id}
            encounter={activeEncounter}
          />
          <OrderCard
            patientId={patient.id}
            ocsList={ocsList}
            onOrderCreated={() => loadPatientData(patient.id)}
          />
        </div>

        {/* 컬럼 2: 과거 기록 */}
        <div className="clinic-column column-2">
          <PastRecordCard
            patientId={patient.id}
            encounters={encounters}
          />
          <CalendarCard
            patientId={patient.id}
            encounters={encounters}
          />
          <LabResultCard
            patientId={patient.id}
            lisResults={lisResults}
          />
        </div>

        {/* 컬럼 3: 일정 */}
        <div className="clinic-column column-3">
          <TodayAppointmentCard />
          <PastPrescriptionCard
            patientId={patient.id}
          />
        </div>
      </div>
    </div>
  );
}

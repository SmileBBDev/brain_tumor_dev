# 작업 지시서: AI 추론 자동/수동 요청 및 Dashboard 업데이트

## 개요

세 가지 주요 작업:
1. AI 추론 자동 요청 시스템 (RIS/LIS 결과 확정 시)
2. 환자 진료 페이지 AI 추론 수동 요청 기능
3. 권한별 Dashboard 기능 업데이트

---

## 1. [Backend] AI 추론 자동 요청 시스템

### 1.1 요구사항
- **M1 (MRI 모델)**: RIS 결과 보고서가 확정되면(`ocs_result = 1`) 자동으로 AI 추론 요청
- **MG (Genetic 모델)**: LIS 결과 보고서가 확정되면(`ocs_result = 1`) 자동으로 AI 추론 요청
- 수동 요청도 계속 가능해야 함

### 1.2 구현 위치

**파일**: `brain_tumor_back/apps/ocs/signals.py` (신규 생성)

```python
from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import OCS
from apps.ai_inference.models import AIModel, AIInferenceRequest
from apps.ai_inference.tasks import trigger_auto_inference  # Celery task

@receiver(post_save, sender=OCS)
def auto_trigger_ai_inference(sender, instance, **kwargs):
    """
    OCS 확정 시 자동 AI 추론 요청
    - RIS 확정 -> M1 모델 자동 요청
    - LIS 확정 -> MG 모델 자동 요청
    """
    # 확정 상태가 아니면 무시
    if instance.ocs_status != OCS.OcsStatus.CONFIRMED:
        return

    # ocs_result가 True(정상)일 때만 자동 추론
    if instance.ocs_result != True:
        return

    # 이미 자동 추론 요청된 경우 스킵 (중복 방지)
    if instance.worker_result.get('_auto_inference_triggered'):
        return

    # 모델 매핑
    model_mapping = {
        'RIS': 'M1',   # RIS 확정 -> M1 (MRI) 모델
        'LIS': 'MG',   # LIS 확정 -> MG (Genetic) 모델
    }

    model_code = model_mapping.get(instance.job_role)
    if not model_code:
        return

    try:
        ai_model = AIModel.objects.get(code=model_code, is_active=True)
    except AIModel.DoesNotExist:
        return

    # 비동기로 AI 추론 요청 생성 (Celery)
    trigger_auto_inference.delay(
        patient_id=instance.patient_id,
        model_code=model_code,
        ocs_id=instance.id,
        triggered_by='auto'
    )

    # 중복 방지 플래그 설정
    instance.worker_result['_auto_inference_triggered'] = True
    instance.save(update_fields=['worker_result'])
```

**파일**: `brain_tumor_back/apps/ocs/apps.py` (수정)

```python
from django.apps import AppConfig

class OcsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.ocs'

    def ready(self):
        import apps.ocs.signals  # 시그널 등록
```

### 1.3 AI 추론 자동 요청 Task

**파일**: `brain_tumor_back/apps/ai_inference/tasks.py` (신규 또는 수정)

```python
from celery import shared_task
from django.utils import timezone
from .models import AIModel, AIInferenceRequest, AIInferenceLog
from apps.patients.models import Patient
from apps.ocs.models import OCS

@shared_task
def trigger_auto_inference(patient_id, model_code, ocs_id, triggered_by='auto'):
    """
    자동 AI 추론 요청 생성
    """
    try:
        patient = Patient.objects.get(id=patient_id)
        model = AIModel.objects.get(code=model_code, is_active=True)
        ocs = OCS.objects.get(id=ocs_id)

        # 이미 동일 OCS에 대해 추론 요청이 있는지 확인
        existing = AIInferenceRequest.objects.filter(
            patient=patient,
            model=model,
            ocs_references__contains=[ocs_id]
        ).exists()

        if existing:
            return {'status': 'skipped', 'reason': 'already_requested'}

        # 추론 요청 생성
        request = AIInferenceRequest.objects.create(
            patient=patient,
            model=model,
            requested_by=ocs.worker or ocs.doctor,  # 작업자 또는 의사
            ocs_references=[ocs_id],
            input_data=_extract_input_data(ocs, model),
            priority=AIInferenceRequest.Priority.NORMAL,
            status=AIInferenceRequest.Status.PENDING
        )

        # 로그 기록
        AIInferenceLog.objects.create(
            inference_request=request,
            action=AIInferenceLog.Action.CREATED,
            message=f'자동 추론 요청 생성 (OCS {ocs.ocs_id} 확정에 의해 트리거)',
            details={'triggered_by': triggered_by, 'ocs_id': ocs_id}
        )

        return {'status': 'created', 'request_id': request.request_id}

    except Exception as e:
        return {'status': 'error', 'error': str(e)}

def _extract_input_data(ocs, model):
    """OCS worker_result에서 AI 모델 입력 데이터 추출"""
    input_data = {}

    for source in model.ocs_sources:
        if source == ocs.job_role:
            required_keys = model.required_keys.get(source, [])
            for key in required_keys:
                value = _get_nested_value(ocs.worker_result, key)
                if value is not None:
                    input_data[f"{source}.{key}"] = value

    return input_data

def _get_nested_value(data, key):
    """중첩 딕셔너리에서 값 추출"""
    if not data:
        return None
    keys = key.split('.')
    value = data
    for k in keys:
        if isinstance(value, dict) and k in value:
            value = value[k]
        else:
            return None
    return value
```

### 1.4 AI 모델 설정 (초기 데이터)

```python
# setup_dummy_data 또는 migration
AIModel.objects.update_or_create(
    code='M1',
    defaults={
        'name': 'MRI 분석 모델',
        'description': 'MRI 영상 기반 뇌종양 분석',
        'ocs_sources': ['RIS'],
        'required_keys': {
            'RIS': ['dicom.study_uid', 'dicom.series']
        },
        'is_active': True
    }
)

AIModel.objects.update_or_create(
    code='MG',
    defaults={
        'name': '유전자 분석 모델',
        'description': 'LIS 유전자 검사 결과 분석',
        'ocs_sources': ['LIS'],
        'required_keys': {
            'LIS': ['test_results', 'gene_mutations']
        },
        'is_active': True
    }
)

AIModel.objects.update_or_create(
    code='MM',
    defaults={
        'name': '멀티모달 분석 모델',
        'description': 'MRI + 유전자 통합 분석',
        'ocs_sources': ['RIS', 'LIS'],
        'required_keys': {
            'RIS': ['dicom.study_uid'],
            'LIS': ['test_results']
        },
        'is_active': True
    }
)
```

---

## 2. [Frontend] 환자 진료 페이지 AI 추론 수동 요청

### 2.1 요구사항
- 환자 진료 페이지에 'AI 추론 요청' 버튼 추가
- 클릭 시 AI 추론 요청 전용 페이지로 이동
- M1, MG, MM 모델 선택 가능

### 2.2 PatientDetailPage.tsx 수정

**파일**: `brain_tumor_front/src/pages/patient/PatientDetailPage.tsx`

버튼 추가 (line 92-111 부근):

```tsx
// 기존 버튼들 아래에 추가
{canCreateOCS && (
  <button
    className="btn btn-ai"
    onClick={() => navigate(`/ai/request?patientId=${patientId}`)}
  >
    AI 추론 요청
  </button>
)}
```

### 2.3 AI 추론 요청 페이지 신규 생성

**파일**: `brain_tumor_front/src/pages/ai/AIRequestPage.tsx` (신규)

```tsx
/**
 * AI 추론 수동 요청 페이지
 * - 환자 정보 표시
 * - 사용 가능한 AI 모델 목록 (M1, MG, MM)
 * - 데이터 충족 여부 표시
 * - 추론 요청 버튼
 */
import { useState, useEffect } from 'react';
import { useSearchParams, useNavigate } from 'react-router-dom';
import { getPatient } from '@/services/patient.api';
import { getAvailableModels, createInferenceRequest } from '@/services/ai.api';
import type { Patient } from '@/types/patient';
import './AIRequestPage.css';

interface AIModelInfo {
  code: string;
  name: string;
  description: string;
  is_available: boolean;
  available_keys: string[];
  missing_keys: string[];
}

export default function AIRequestPage() {
  const [params] = useSearchParams();
  const navigate = useNavigate();
  const patientId = params.get('patientId');

  const [patient, setPatient] = useState<Patient | null>(null);
  const [models, setModels] = useState<AIModelInfo[]>([]);
  const [selectedModel, setSelectedModel] = useState<string>('');
  const [loading, setLoading] = useState(true);
  const [requesting, setRequesting] = useState(false);

  useEffect(() => {
    if (!patientId) return;

    const fetchData = async () => {
      try {
        const [patientData, modelsData] = await Promise.all([
          getPatient(Number(patientId)),
          getAvailableModels(Number(patientId))
        ]);
        setPatient(patientData);
        setModels(modelsData);
      } catch (err) {
        console.error(err);
        alert('데이터를 불러오는데 실패했습니다.');
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, [patientId]);

  const handleRequest = async () => {
    if (!selectedModel || !patientId) return;

    setRequesting(true);
    try {
      const result = await createInferenceRequest({
        patient_id: Number(patientId),
        model_code: selectedModel
      });
      alert(`AI 추론 요청이 생성되었습니다. (${result.request_id})`);
      navigate(`/ai/requests/${result.id}`);
    } catch (err) {
      console.error(err);
      alert('추론 요청에 실패했습니다.');
    } finally {
      setRequesting(false);
    }
  };

  if (loading) return <div className="page ai-request">로딩 중...</div>;
  if (!patient) return <div className="page ai-request">환자를 찾을 수 없습니다.</div>;

  return (
    <div className="page ai-request">
      <header className="page-header">
        <h1>AI 추론 요청</h1>
        <button className="btn" onClick={() => navigate(-1)}>뒤로가기</button>
      </header>

      {/* 환자 정보 */}
      <section className="patient-info-bar">
        <div className="info-item">
          <span>환자번호:</span>
          <span>{patient.patient_number}</span>
        </div>
        <div className="info-item">
          <span>이름:</span>
          <span>{patient.name}</span>
        </div>
      </section>

      {/* AI 모델 선택 */}
      <section className="model-selection">
        <h2>AI 모델 선택</h2>
        <div className="model-list">
          {models.map((model) => (
            <div
              key={model.code}
              className={`model-card ${selectedModel === model.code ? 'selected' : ''} ${!model.is_available ? 'disabled' : ''}`}
              onClick={() => model.is_available && setSelectedModel(model.code)}
            >
              <div className="model-header">
                <span className="model-code">{model.code}</span>
                <span className="model-name">{model.name}</span>
                {model.is_available ? (
                  <span className="badge available">사용 가능</span>
                ) : (
                  <span className="badge unavailable">데이터 부족</span>
                )}
              </div>
              <p className="model-description">{model.description}</p>

              {!model.is_available && model.missing_keys.length > 0 && (
                <div className="missing-data">
                  <strong>필요 데이터:</strong>
                  <ul>
                    {model.missing_keys.map((key) => (
                      <li key={key}>{key}</li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
          ))}
        </div>
      </section>

      {/* 요청 버튼 */}
      <div className="action-bar">
        <button
          className="btn btn-primary btn-lg"
          onClick={handleRequest}
          disabled={!selectedModel || requesting}
        >
          {requesting ? '요청 중...' : 'AI 추론 요청'}
        </button>
      </div>
    </div>
  );
}
```

### 2.4 AI API 서비스

**파일**: `brain_tumor_front/src/services/ai.api.ts` (신규 또는 수정)

```typescript
import api from './api';

export interface AIModelInfo {
  code: string;
  name: string;
  description: string;
  is_available: boolean;
  available_keys: string[];
  missing_keys: string[];
}

export interface CreateInferenceRequest {
  patient_id: number;
  model_code: string;
  priority?: 'low' | 'normal' | 'high' | 'urgent';
}

export const getAvailableModels = async (patientId: number): Promise<AIModelInfo[]> => {
  const response = await api.get(`/ai/patients/${patientId}/available-models/`);
  return response.data;
};

export const createInferenceRequest = async (data: CreateInferenceRequest) => {
  const response = await api.post('/ai/requests/', data);
  return response.data;
};

export const getInferenceRequest = async (requestId: number) => {
  const response = await api.get(`/ai/requests/${requestId}/`);
  return response.data;
};

export const getPatientInferenceHistory = async (patientId: number) => {
  const response = await api.get(`/ai/patients/${patientId}/requests/`);
  return response.data;
};
```

### 2.5 라우팅 추가

**파일**: `brain_tumor_front/src/router/AppRoutes.tsx`

```tsx
// AI 추론 관련 라우트 추가
<Route path="/ai/request" element={<AIRequestPage />} />
<Route path="/ai/requests/:requestId" element={<AIRequestDetailPage />} />
```

---

## 3. [Frontend] 권한별 Dashboard 기능 업데이트

### 3.1 현재 구조

| 권한 | Dashboard 컴포넌트 | 상태 |
|------|---------------------|------|
| DOCTOR | DoctorDashboard | 구현됨 |
| NURSE | NurseDashboard | 구현됨 |
| LIS | LISDashboard | 구현됨 |
| RIS | RISDashboard | 구현됨 |
| SYSTEMMANAGER | SystemManagerDashboard | 구현됨 |
| PATIENT | PatientDashboard | 구현됨 |
| ADMIN | CommingSoon | 미구현 |

### 3.2 각 Dashboard 업데이트 사항

#### 3.2.1 DoctorDashboard 업데이트

**파일**: `brain_tumor_front/src/pages/dashboard/doctor/DoctorDashboard.tsx`

```tsx
import { DoctorSummaryCards } from "./DoctorSummaryCards";
import { DoctorWorklist } from "./DoctorWorklist";
import { AiAlertPanel } from "./AiAlertPanel";
import { RecentPatients } from "./RecentPatients";
import { AIInferenceStatusPanel } from "./AIInferenceStatusPanel";  // 신규

export default function DoctorDashboard() {
  return (
    <div className="dashboard doctor">
      <DoctorSummaryCards />
      <div className="dashboard-row">
        <DoctorWorklist />
        <div className="dashboard-col">
          <AiAlertPanel />
          <AIInferenceStatusPanel />  {/* AI 추론 현황 패널 */}
        </div>
      </div>
      <RecentPatients />
    </div>
  );
}
```

**AIInferenceStatusPanel 컴포넌트** (신규):
- 최근 AI 추론 요청 상태 표시
- 대기 중 / 처리 중 / 완료 개수
- 검토 필요한 결과 알림

#### 3.2.2 NurseDashboard 업데이트

현재 기능 유지 + 환자 상태 모니터링 강화

#### 3.2.3 LISDashboard 업데이트

```tsx
// 추가 기능
- 확정 대기 중인 검사 결과 목록
- AI 자동 추론 트리거 상태 표시
- 외부 기관 데이터 업로드 현황
```

#### 3.2.4 RISDashboard 업데이트

```tsx
// 추가 기능
- 확정 대기 중인 영상 판독 목록
- AI 자동 추론 트리거 상태 표시
- DICOM 업로드 현황
```

#### 3.2.5 SystemManagerDashboard 업데이트

이미 구현된 탭 기능 유지:
- DOCTOR, NURSE, LIS, RIS, PATIENT 탭 전환
- 각 역할별 Dashboard 미리보기

추가 기능:
```tsx
// 시스템 전체 현황 탭 추가
- 전체 OCS 통계
- AI 추론 요청 통계
- 사용자별 활동 로그
```

### 3.3 DashboardRouter 수정

**파일**: `brain_tumor_front/src/pages/dashboard/DashboardRouter.tsx`

```tsx
import DoctorDashboard from '@/pages/dashboard/doctor/DoctorDashboard';
import NurseDashboard from '@/pages/dashboard/nurse/NurseDashboard';
import LISDashboard from '@/pages/dashboard/lis/LISDashboard';
import RISDashboard from '@/pages/dashboard/ris/RISDashboard';
import SystemManagerDashboard from './systemManager/SystemManagerDashboard';
import PatientDashboard from '@/pages/patient/PatientDashboard';  // 실제 환자용
import AdminDashboard from './admin/AdminDashboard';  // 신규

interface Props {
  role: string;
}

export default function DashboardRouter({ role }: Props) {
  switch (role) {
    case 'DOCTOR':
      return <DoctorDashboard />;
    case 'NURSE':
      return <NurseDashboard />;
    case 'LIS':
      return <LISDashboard />;
    case 'RIS':
      return <RISDashboard />;
    case 'SYSTEMMANAGER':
      return <SystemManagerDashboard />;
    case 'PATIENT':
      return <PatientDashboard />;  // 실제 환자 대시보드
    case 'ADMIN':
      return <AdminDashboard />;
    default:
      return <div>대시보드를 찾을 수 없습니다.</div>;
  }
}
```

---

## 4. API 엔드포인트 정리

### AI 추론 관련

| Method | Endpoint | 설명 |
|--------|----------|------|
| GET | `/api/ai/models/` | AI 모델 목록 |
| GET | `/api/ai/patients/{id}/available-models/` | 환자별 사용 가능 모델 |
| POST | `/api/ai/requests/` | 추론 요청 생성 |
| GET | `/api/ai/requests/{id}/` | 요청 상세 |
| GET | `/api/ai/requests/{id}/status/` | 요청 상태 |
| POST | `/api/ai/requests/{id}/cancel/` | 요청 취소 |
| GET | `/api/ai/results/` | 결과 목록 |
| POST | `/api/ai/results/{id}/review/` | 결과 검토 |

---

## 5. 작업 분담

### Backend 작업
1. [ ] `ocs/signals.py` 생성 - OCS 확정 시 자동 추론 트리거
2. [ ] `ai_inference/tasks.py` - Celery 자동 추론 태스크
3. [ ] AI 모델 초기 데이터 (M1, MG, MM) 설정
4. [ ] 자동 추론 중복 방지 로직

### Frontend 작업
1. [ ] `PatientDetailPage.tsx` - AI 추론 요청 버튼 추가
2. [ ] `AIRequestPage.tsx` - AI 추론 요청 전용 페이지
3. [ ] `ai.api.ts` - AI 관련 API 서비스
4. [ ] Dashboard 업데이트
   - [ ] DoctorDashboard - AI 추론 현황 패널
   - [ ] LISDashboard - 확정 대기 목록
   - [ ] RISDashboard - 확정 대기 목록
5. [ ] 라우팅 추가 (`/ai/request`, `/ai/requests/:id`)

---

## 6. 테스트 시나리오

### 자동 추론 테스트
1. RIS 오더 생성 -> 작업 진행 -> 결과 제출 -> 확정
2. 확정 시 M1 모델 자동 추론 요청 생성 확인
3. LIS 오더 동일 흐름으로 MG 모델 자동 추론 확인

### 수동 추론 테스트
1. 환자 진료 페이지 접속
2. 'AI 추론 요청' 버튼 클릭
3. 사용 가능한 모델 확인 (데이터 충족 여부)
4. 모델 선택 후 요청
5. 요청 상태 확인

### Dashboard 테스트
1. 각 권한별 로그인
2. Dashboard 표시 확인
3. AI 추론 현황 표시 확인 (Doctor)

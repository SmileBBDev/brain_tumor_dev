# B 에이전트 (Frontend)

## 담당 영역
- `brain_tumor_front/` (React + TypeScript)
- 컴포넌트, 페이지, 서비스, 타입

## 규칙
- API 응답 방어적 처리: `Array.isArray(data) ? data : data?.results || []`
- 타입 정의 필수
- 기존 CSS 패턴 따르기

## 참고 문서
- `SHARED.md`: 공용 정보 (비밀번호, 역할, 경로)
- `PROJECT_DOCS.md`: 프로젝트 아키텍처
- `AI_MODELS.md`: AI 모델 정의 (M1, MG, MM)
- `TODO_BACKLOG.md`: 전체 백로그

## 주의사항
- AI 추론 관련 페이지(`pages/ai-inference/`)는 **다른 작업자가 작업 중** - 건드리지 말 것

---

## 현재 작업 (2026-01-12)

### 작업 1: ClinicPage에 AI 수동 요청 버튼 추가

**수정 파일**: `src/pages/clinic/components/ExaminationTab.tsx`

검사 오더 섹션 아래에 AI 추론 요청 섹션 추가:

```tsx
{/* AI 추론 요청 섹션 - 검사 오더 섹션 아래에 추가 */}
<section className="exam-section ai-request-card">
  <div className="section-header">
    <h4>
      <span className="card-icon">🤖</span>
      AI 추론 요청
    </h4>
    <button
      className="btn btn-sm btn-primary"
      onClick={() => navigate(`/ai/requests/create?patientId=${patientId}`)}
    >
      AI 추론 요청
    </button>
  </div>
  <div className="ai-model-info">
    <p className="info-text">환자의 검사 데이터를 기반으로 AI 분석을 요청합니다.</p>
    <div className="model-badges">
      <span className="model-badge" title="MRI 4-Channel (T1, T2, T1C, FLAIR)">M1 - MRI 분석</span>
      <span className="model-badge" title="Genetic Analysis (RNA_seq)">MG - 유전자 분석</span>
      <span className="model-badge" title="Multimodal (MRI + 유전 + 단백질)">MM - 멀티모달</span>
    </div>
  </div>
</section>
```

**CSS 추가**:

```css
/* AI Request Card */
.ai-request-card {
  background: linear-gradient(135deg, #f5f7ff 0%, #fff 100%);
  border: 1px solid #e3e8ff;
}

.ai-model-info {
  padding: 12px 0;
}

.ai-model-info .info-text {
  font-size: 13px;
  color: #666;
  margin-bottom: 12px;
}

.model-badges {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}

.model-badge {
  display: inline-block;
  padding: 4px 12px;
  background: #e3f2fd;
  color: #1565c0;
  border-radius: 16px;
  font-size: 12px;
  cursor: help;
}
```

**연결 포인트**:
- 라우팅: `/ai/requests/create?patientId={id}` (이미 동작)
- API: `POST /api/ai/requests/` (이미 구현됨)

---

### 작업 2: Dashboard API 서비스 생성

**새 파일**: `src/services/dashboard.api.ts`

```typescript
import { api } from './api';

// Admin Dashboard 통계
export interface AdminStats {
  users: {
    total: number;
    by_role: Record<string, number>;
    recent_logins: number;
  };
  patients: {
    total: number;
    new_this_month: number;
  };
  ocs: {
    total: number;
    by_status: Record<string, number>;
    pending_count: number;
  };
}

// External Dashboard 통계
export interface ExternalStats {
  lis_uploads: {
    pending: number;
    completed: number;
    total_this_week: number;
  };
  ris_uploads: {
    pending: number;
    completed: number;
    total_this_week: number;
  };
  recent_uploads: Array<{
    id: number;
    ocs_id: string;
    job_role: string;
    status: string;
    uploaded_at: string;
    patient_name: string;
  }>;
}

export const getAdminStats = async (): Promise<AdminStats> => {
  const response = await api.get('/dashboard/admin/stats/');
  return response.data;
};

export const getExternalStats = async (): Promise<ExternalStats> => {
  const response = await api.get('/dashboard/external/stats/');
  return response.data;
};
```

---

### 작업 3: AdminDashboard 컴포넌트 생성

**새 파일**: `src/pages/dashboard/admin/AdminDashboard.tsx`

```tsx
import { useState, useEffect } from 'react';
import { getAdminStats, AdminStats } from '@/services/dashboard.api';
import './AdminDashboard.css';

export default function AdminDashboard() {
  const [stats, setStats] = useState<AdminStats | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchStats = async () => {
      try {
        const data = await getAdminStats();
        setStats(data);
      } catch (err) {
        console.error('Failed to fetch admin stats:', err);
      } finally {
        setLoading(false);
      }
    };
    fetchStats();
  }, []);

  if (loading) return <div className="loading">통계 로딩 중...</div>;
  if (!stats) return <div className="error">통계를 불러올 수 없습니다.</div>;

  return (
    <div className="admin-dashboard">
      <h2>관리자 대시보드</h2>

      {/* 요약 카드 */}
      <div className="summary-cards">
        <div className="summary-card users">
          <div className="card-icon">👥</div>
          <div className="card-content">
            <span className="card-value">{stats.users.total}</span>
            <span className="card-label">전체 사용자</span>
            <span className="card-sub">최근 로그인: {stats.users.recent_logins}명</span>
          </div>
        </div>

        <div className="summary-card patients">
          <div className="card-icon">🏥</div>
          <div className="card-content">
            <span className="card-value">{stats.patients.total}</span>
            <span className="card-label">전체 환자</span>
            <span className="card-sub">이번 달 신규: {stats.patients.new_this_month}명</span>
          </div>
        </div>

        <div className="summary-card ocs">
          <div className="card-icon">📋</div>
          <div className="card-content">
            <span className="card-value">{stats.ocs.total}</span>
            <span className="card-label">OCS 현황</span>
            <span className="card-sub">대기 중: {stats.ocs.pending_count}건</span>
          </div>
        </div>
      </div>

      {/* OCS 상태별 현황 */}
      <div className="dashboard-section">
        <h3>OCS 상태별 현황</h3>
        <div className="status-grid">
          {Object.entries(stats.ocs.by_status).map(([status, count]) => (
            <div key={status} className={`status-item status-${status.toLowerCase()}`}>
              <span className="status-label">{status}</span>
              <span className="status-count">{count}</span>
            </div>
          ))}
        </div>
      </div>

      {/* 역할별 사용자 현황 */}
      <div className="dashboard-section">
        <h3>역할별 사용자</h3>
        <div className="role-grid">
          {Object.entries(stats.users.by_role).map(([role, count]) => (
            <div key={role} className="role-item">
              <span className="role-name">{role}</span>
              <span className="role-count">{count}명</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
```

**새 파일**: `src/pages/dashboard/admin/AdminDashboard.css`

```css
.admin-dashboard {
  padding: 24px;
}

.admin-dashboard h2 {
  margin-bottom: 24px;
  font-size: 24px;
  font-weight: 600;
}

.admin-dashboard .summary-cards {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 16px;
  margin-bottom: 32px;
}

.admin-dashboard .summary-card {
  background: #fff;
  border-radius: 12px;
  padding: 20px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
  display: flex;
  align-items: center;
  gap: 16px;
}

.admin-dashboard .card-icon {
  font-size: 32px;
}

.admin-dashboard .card-content {
  display: flex;
  flex-direction: column;
}

.admin-dashboard .card-value {
  font-size: 28px;
  font-weight: 700;
}

.admin-dashboard .card-label {
  font-size: 14px;
  color: #666;
}

.admin-dashboard .card-sub {
  font-size: 12px;
  color: #999;
  margin-top: 4px;
}

.admin-dashboard .dashboard-section {
  background: #fff;
  border-radius: 12px;
  padding: 20px 24px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
  margin-bottom: 24px;
}

.admin-dashboard .dashboard-section h3 {
  font-size: 16px;
  margin-bottom: 16px;
}

.admin-dashboard .status-grid,
.admin-dashboard .role-grid {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
}

.admin-dashboard .status-item,
.admin-dashboard .role-item {
  padding: 8px 16px;
  background: #f5f5f5;
  border-radius: 8px;
  display: flex;
  gap: 8px;
  align-items: center;
}

.admin-dashboard .status-count,
.admin-dashboard .role-count {
  font-weight: 600;
}

@media (max-width: 1200px) {
  .admin-dashboard .summary-cards {
    grid-template-columns: repeat(2, 1fr);
  }
}
```

---

### 작업 4: ExternalDashboard 컴포넌트 생성

**새 파일**: `src/pages/dashboard/external/ExternalDashboard.tsx`

```tsx
import { useState, useEffect } from 'react';
import { getExternalStats, ExternalStats } from '@/services/dashboard.api';
import './ExternalDashboard.css';

export default function ExternalDashboard() {
  const [stats, setStats] = useState<ExternalStats | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchStats = async () => {
      try {
        const data = await getExternalStats();
        setStats(data);
      } catch (err) {
        console.error('Failed to fetch external stats:', err);
      } finally {
        setLoading(false);
      }
    };
    fetchStats();
  }, []);

  if (loading) return <div className="loading">통계 로딩 중...</div>;
  if (!stats) return <div className="error">통계를 불러올 수 없습니다.</div>;

  return (
    <div className="external-dashboard">
      <h2>외부기관 업로드 현황</h2>

      {/* 요약 카드 */}
      <div className="summary-cards">
        <div className="summary-card lis">
          <h3>🧬 LIS 업로드</h3>
          <div className="card-stats">
            <div className="stat pending">
              <span className="stat-value">{stats.lis_uploads.pending}</span>
              <span className="stat-label">대기 중</span>
            </div>
            <div className="stat completed">
              <span className="stat-value">{stats.lis_uploads.completed}</span>
              <span className="stat-label">완료</span>
            </div>
          </div>
          <span className="card-sub">이번 주: {stats.lis_uploads.total_this_week}건</span>
        </div>

        <div className="summary-card ris">
          <h3>🩻 RIS 업로드</h3>
          <div className="card-stats">
            <div className="stat pending">
              <span className="stat-value">{stats.ris_uploads.pending}</span>
              <span className="stat-label">대기 중</span>
            </div>
            <div className="stat completed">
              <span className="stat-value">{stats.ris_uploads.completed}</span>
              <span className="stat-label">완료</span>
            </div>
          </div>
          <span className="card-sub">이번 주: {stats.ris_uploads.total_this_week}건</span>
        </div>
      </div>

      {/* 최근 업로드 목록 */}
      <div className="dashboard-section">
        <h3>최근 업로드</h3>
        <table className="upload-table">
          <thead>
            <tr>
              <th>OCS ID</th>
              <th>환자</th>
              <th>유형</th>
              <th>상태</th>
              <th>업로드 시간</th>
            </tr>
          </thead>
          <tbody>
            {stats.recent_uploads.length === 0 ? (
              <tr>
                <td colSpan={5} className="empty">업로드 내역이 없습니다.</td>
              </tr>
            ) : (
              stats.recent_uploads.map((upload) => (
                <tr key={upload.id}>
                  <td>{upload.ocs_id}</td>
                  <td>{upload.patient_name}</td>
                  <td>{upload.job_role}</td>
                  <td>
                    <span className={`status-badge status-${upload.status.toLowerCase()}`}>
                      {upload.status}
                    </span>
                  </td>
                  <td>{new Date(upload.uploaded_at).toLocaleString('ko-KR')}</td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}
```

**새 파일**: `src/pages/dashboard/external/ExternalDashboard.css`

```css
.external-dashboard {
  padding: 24px;
}

.external-dashboard h2 {
  margin-bottom: 24px;
  font-size: 24px;
  font-weight: 600;
}

.external-dashboard .summary-cards {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 16px;
  margin-bottom: 32px;
}

.external-dashboard .summary-card {
  background: #fff;
  border-radius: 12px;
  padding: 20px 24px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
}

.external-dashboard .summary-card h3 {
  font-size: 16px;
  margin-bottom: 16px;
}

.external-dashboard .card-stats {
  display: flex;
  gap: 24px;
  margin-bottom: 12px;
}

.external-dashboard .stat {
  display: flex;
  flex-direction: column;
}

.external-dashboard .stat-value {
  font-size: 32px;
  font-weight: 700;
}

.external-dashboard .stat.pending .stat-value {
  color: #e67e22;
}

.external-dashboard .stat.completed .stat-value {
  color: #27ae60;
}

.external-dashboard .stat-label {
  font-size: 13px;
  color: #666;
}

.external-dashboard .card-sub {
  font-size: 12px;
  color: #999;
}

.external-dashboard .dashboard-section {
  background: #fff;
  border-radius: 12px;
  padding: 20px 24px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
}

.external-dashboard .dashboard-section h3 {
  font-size: 16px;
  margin-bottom: 16px;
}

.external-dashboard .upload-table {
  width: 100%;
  border-collapse: collapse;
}

.external-dashboard .upload-table th,
.external-dashboard .upload-table td {
  padding: 12px;
  text-align: left;
  border-bottom: 1px solid #eee;
}

.external-dashboard .upload-table th {
  font-weight: 600;
  background: #f9f9f9;
}

.external-dashboard .upload-table .empty {
  text-align: center;
  color: #999;
  padding: 24px;
}

.external-dashboard .status-badge {
  padding: 4px 8px;
  border-radius: 4px;
  font-size: 12px;
}

.external-dashboard .status-badge.status-result_ready {
  background: #fff3e0;
  color: #e67e22;
}

.external-dashboard .status-badge.status-confirmed {
  background: #e8f5e9;
  color: #27ae60;
}
```

---

### 작업 5: DashboardRouter 수정

**수정 파일**: `src/pages/dashboard/DashboardRouter.tsx`

```tsx
// import 추가
import AdminDashboard from './admin/AdminDashboard';
import ExternalDashboard from './external/ExternalDashboard';

// switch문 수정
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
    case 'ADMIN':
      return <AdminDashboard />;      // CommingSoon → AdminDashboard
    case 'EXTERNAL':
      return <ExternalDashboard />;   // 새로 추가
    default:
      return <div>대시보드를 찾을 수 없습니다.</div>;
  }
}
```

---

## 완료 기준

- [ ] ExaminationTab.tsx에 AI 추론 요청 섹션 추가
- [ ] dashboard.api.ts 생성
- [ ] AdminDashboard 컴포넌트 생성 (tsx + css)
- [ ] ExternalDashboard 컴포넌트 생성 (tsx + css)
- [ ] DashboardRouter에 ADMIN/EXTERNAL 케이스 추가
- [ ] 테스트: doctor1 로그인 → ClinicPage에서 AI 요청 버튼 확인
- [ ] 테스트: admin 로그인 → AdminDashboard 표시 확인

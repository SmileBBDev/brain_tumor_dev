import type { Role } from '@/types/role';
import {useState} from 'react';
import PatientListHeader from './PatientListHeader';
import PatientListTable from './PatientListTable';
import Pagination from '@/layout/Pagination';

export default function PatientListPage() {
  const role = localStorage.getItem('role') as Role | null;
  const isSystemManager = role === 'SYSTEMMANAGER';
  const [page, setPage] = useState(1); // 페이징 처리

  if (!role) {
    return <div>접근 권한 정보 없음</div>;
  }

  return (
    <div className="page patient-list">
      {/* 검색 / 필터 영역 (환자 외의 역할에만 표시) */}
       {role !== 'PATIENT' && (
        <section  className="filter-bar">
          <div className="filter-left">
            <strong className="patient-count">
              총 <span>totalCount</span>명의 환자가 있습니다.&nbsp;&nbsp;
            </strong>
            <input placeholder="환자명 / 환자 ID" />
          </div>
          <div className="filter-right">
            <select>
              <option>전체 상태</option>
              <option>진료중</option>
              <option>완료</option>
            </select>

            <select>
              <option>진료 유형</option>
              <option>외래</option>
              <option>병동</option>
            </select>

            <select>
              <option>성별</option>
              <option>남성</option>
              <option>여성</option>
            </select>
          </div>
        </section >
      )}

      <div className="header-right">
        {(role === 'DOCTOR' || role === 'NURSE' || isSystemManager) && (
          <button className="btn primary">
            <i className="fa-solid fa-user-plus"></i>
            &nbsp;
            <span>환자 등록</span>
          </button>
        )}
      </div>

      {/* 환자 리스트 테이블 */}
      <section className="content">
        <PatientListTable role={role}/>
      </section>

      {/* 페이징 */}
      <section className="pagination-bar">
        <Pagination
          // currentPage={page}
          // 👉 임시 값 (API 붙이면 교체)
          currentPage={page}
          totalPages={20} 
          onChange={setPage}
          pageSize={5}
        />
      </section>

    </div>
  );
}

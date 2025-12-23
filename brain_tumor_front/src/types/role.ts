// Role 타입 정의(역할 정의)
// TODO : DB에서 Role 어떻게 받아오는지 확인 후 코드 수정
export type Role =
    |'SYSTEMMANAGER' // 시스템 관리자
    |'ADMIN' // 관리자
    |'DOCTOR' // 의사
    |'NURSE' // 간호사
    |'RIS' // 영상과
    |'LIS' // 검사과
    |'PATIENT' // 환자
;
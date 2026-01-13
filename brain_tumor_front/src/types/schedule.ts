/**
 * 의사 일정 관련 타입 정의
 */

// 일정 유형
export type ScheduleType = 'meeting' | 'leave' | 'training' | 'personal' | 'other';

// 일정 유형 라벨
export const SCHEDULE_TYPE_LABELS: Record<ScheduleType, string> = {
  meeting: '회의',
  leave: '휴가',
  training: '교육',
  personal: '개인',
  other: '기타',
};

// 일정 유형별 기본 색상
export const SCHEDULE_TYPE_COLORS: Record<ScheduleType, string> = {
  meeting: '#5b8def',
  leave: '#e56b6f',
  training: '#f2a65a',
  personal: '#5fb3a2',
  other: '#9ca3af',
};

// 일정 목록 아이템
export interface DoctorScheduleListItem {
  id: number;
  title: string;
  schedule_type: ScheduleType;
  schedule_type_display: string;
  start_datetime: string;
  end_datetime: string;
  all_day: boolean;
  color: string;
}

// 일정 상세
export interface DoctorScheduleDetail extends DoctorScheduleListItem {
  description: string;
  doctor: number;
  doctor_name: string;
  created_at: string;
  updated_at: string;
}

// 일정 생성 요청
export interface DoctorScheduleCreateRequest {
  title: string;
  schedule_type: ScheduleType;
  start_datetime: string;
  end_datetime: string;
  all_day?: boolean;
  description?: string;
  color?: string;
}

// 일정 수정 요청
export interface DoctorScheduleUpdateRequest {
  title?: string;
  schedule_type?: ScheduleType;
  start_datetime?: string;
  end_datetime?: string;
  all_day?: boolean;
  description?: string;
  color?: string;
}

// 캘린더용 일정 아이템
export interface CalendarScheduleItem {
  id: number;
  title: string;
  schedule_type: ScheduleType;
  start: string;
  end: string;
  all_day: boolean;
  color: string;
}

// 캘린더 조회 파라미터
export interface ScheduleCalendarParams {
  year: number;
  month: number;
}

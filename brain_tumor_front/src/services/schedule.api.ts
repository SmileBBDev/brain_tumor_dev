import { api } from './api';
import type {
  DoctorScheduleListItem,
  DoctorScheduleDetail,
  DoctorScheduleCreateRequest,
  DoctorScheduleUpdateRequest,
  CalendarScheduleItem,
  ScheduleCalendarParams,
} from '@/types/schedule';

/**
 * 의사 일정 API Service
 */

// =============================================================================
// 기본 CRUD
// =============================================================================

// 일정 목록 조회
export const getScheduleList = async (): Promise<DoctorScheduleListItem[]> => {
  const response = await api.get<DoctorScheduleListItem[]>('/schedules/');
  return response.data;
};

// 일정 상세 조회
export const getSchedule = async (scheduleId: number): Promise<DoctorScheduleDetail> => {
  const response = await api.get<DoctorScheduleDetail>(`/schedules/${scheduleId}/`);
  return response.data;
};

// 일정 생성
export const createSchedule = async (data: DoctorScheduleCreateRequest): Promise<DoctorScheduleDetail> => {
  const response = await api.post<DoctorScheduleDetail>('/schedules/', data);
  return response.data;
};

// 일정 수정
export const updateSchedule = async (
  scheduleId: number,
  data: DoctorScheduleUpdateRequest
): Promise<DoctorScheduleDetail> => {
  const response = await api.patch<DoctorScheduleDetail>(`/schedules/${scheduleId}/`, data);
  return response.data;
};

// 일정 삭제
export const deleteSchedule = async (scheduleId: number): Promise<void> => {
  await api.delete(`/schedules/${scheduleId}/`);
};

// =============================================================================
// 추가 조회 API
// =============================================================================

// 캘린더 조회 (월별)
export const getScheduleCalendar = async (params: ScheduleCalendarParams): Promise<CalendarScheduleItem[]> => {
  const response = await api.get<CalendarScheduleItem[]>('/schedules/calendar/', { params });
  return response.data;
};

// 오늘 일정 조회
export const getTodaySchedules = async (): Promise<DoctorScheduleListItem[]> => {
  const response = await api.get<DoctorScheduleListItem[]>('/schedules/today/');
  return response.data;
};

// 이번 주 일정 조회
export const getThisWeekSchedules = async (): Promise<DoctorScheduleListItem[]> => {
  const response = await api.get<DoctorScheduleListItem[]>('/schedules/this-week/');
  return response.data;
};

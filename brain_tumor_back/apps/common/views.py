import logging

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.utils import timezone
from django.db.models import Count, Q
from datetime import timedelta
from drf_spectacular.utils import extend_schema, OpenApiResponse

from apps.accounts.models import User
from apps.patients.models import Patient
from apps.ocs.models import OCS
from apps.encounters.models import Encounter
from apps.common.permission import IsAdmin, IsExternalOrAdmin, IsDoctorOrAdmin

logger = logging.getLogger(__name__)


@extend_schema(
    tags=["Dashboard"],
    summary="관리자 대시보드 통계",
    description="관리자용 대시보드 통계를 조회합니다. ADMIN, SYSTEMMANAGER 역할 접근 가능합니다.",
    responses={
        200: OpenApiResponse(description="통계 조회 성공"),
        403: OpenApiResponse(description="권한 없음"),
        500: OpenApiResponse(description="서버 오류"),
    }
)
class AdminDashboardStatsView(APIView):
    """관리자 대시보드 통계 API"""
    permission_classes = [IsAdmin]

    def get(self, request):
        try:
            now = timezone.now()
            month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            week_ago = now - timedelta(days=7)

            # 사용자 통계
            users = User.objects.filter(is_active=True)
            user_by_role = dict(
                users.values('role__code')
                .annotate(count=Count('id'))
                .values_list('role__code', 'count')
            )

            # 환자 통계
            patients = Patient.objects.filter(is_deleted=False)

            # OCS 통계
            ocs_all = OCS.objects.filter(is_deleted=False)
            ocs_by_status = dict(
                ocs_all.values('ocs_status')
                .annotate(count=Count('id'))
                .values_list('ocs_status', 'count')
            )

            return Response({
                'users': {
                    'total': users.count(),
                    'by_role': user_by_role,
                    'recent_logins': users.filter(last_login__gte=week_ago).count(),
                },
                'patients': {
                    'total': patients.count(),
                    'new_this_month': patients.filter(created_at__gte=month_start).count(),
                },
                'ocs': {
                    'total': ocs_all.count(),
                    'by_status': ocs_by_status,
                    'pending_count': ocs_all.filter(
                        ocs_status__in=[
                            OCS.OcsStatus.ORDERED,
                            OCS.OcsStatus.ACCEPTED,
                            OCS.OcsStatus.IN_PROGRESS
                        ]
                    ).count(),
                },
            })
        except Exception as e:
            logger.error(f"Admin dashboard stats error: {str(e)}")
            return Response(
                {'error': '통계를 불러오는 중 오류가 발생했습니다.'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


@extend_schema(
    tags=["Dashboard"],
    summary="외부기관 대시보드 통계",
    description="외부기관용 대시보드 통계를 조회합니다. EXTERNAL, ADMIN, SYSTEMMANAGER 역할 접근 가능합니다.",
    responses={
        200: OpenApiResponse(description="통계 조회 성공"),
        403: OpenApiResponse(description="권한 없음"),
        500: OpenApiResponse(description="서버 오류"),
    }
)
class ExternalDashboardStatsView(APIView):
    """외부기관 대시보드 통계 API"""
    permission_classes = [IsExternalOrAdmin]

    def get(self, request):
        try:
            now = timezone.now()
            week_ago = now - timedelta(days=7)

            # 외부 LIS 업로드 (extr_ prefix)
            lis_external = OCS.objects.filter(
                ocs_id__startswith='extr_',
                job_role='LIS',
                is_deleted=False
            )

            # 외부 RIS 업로드 (risx_ prefix)
            ris_external = OCS.objects.filter(
                ocs_id__startswith='risx_',
                job_role='RIS',
                is_deleted=False
            )

            # 최근 업로드
            recent = OCS.objects.filter(
                Q(ocs_id__startswith='extr_') | Q(ocs_id__startswith='risx_'),
                is_deleted=False
            ).select_related('patient').order_by('-created_at')[:10]

            return Response({
                'lis_uploads': {
                    'pending': lis_external.filter(ocs_status=OCS.OcsStatus.RESULT_READY).count(),
                    'completed': lis_external.filter(ocs_status=OCS.OcsStatus.CONFIRMED).count(),
                    'total_this_week': lis_external.filter(created_at__gte=week_ago).count(),
                },
                'ris_uploads': {
                    'pending': ris_external.filter(ocs_status=OCS.OcsStatus.RESULT_READY).count(),
                    'completed': ris_external.filter(ocs_status=OCS.OcsStatus.CONFIRMED).count(),
                    'total_this_week': ris_external.filter(created_at__gte=week_ago).count(),
                },
                'recent_uploads': [
                    {
                        'id': o.id,
                        'ocs_id': o.ocs_id,
                        'job_role': o.job_role,
                        'status': o.ocs_status,
                        'uploaded_at': o.created_at.isoformat(),
                        'patient_name': o.patient.name if o.patient else '-',
                    }
                    for o in recent
                ],
            })
        except Exception as e:
            logger.error(f"External dashboard stats error: {str(e)}")
            return Response(
                {'error': '통계를 불러오는 중 오류가 발생했습니다.'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


@extend_schema(
    tags=["Dashboard"],
    summary="의사 대시보드 통계",
    description="의사용 대시보드 통계를 조회합니다. DOCTOR, ADMIN, SYSTEMMANAGER 역할 접근 가능합니다. 금일 예약 환자 5명을 반환합니다.",
    responses={
        200: OpenApiResponse(description="통계 조회 성공"),
        403: OpenApiResponse(description="권한 없음"),
        500: OpenApiResponse(description="서버 오류"),
    }
)
class DoctorDashboardStatsView(APIView):
    """의사 대시보드 통계 API"""
    permission_classes = [IsDoctorOrAdmin]

    def get(self, request):
        try:
            now = timezone.now()
            today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
            today_end = today_start + timedelta(days=1)

            # 전체 금일 통계 (상태별) - cancelled 제외
            all_today = Encounter.objects.filter(
                attending_doctor=request.user,
                admission_date__gte=today_start,
                admission_date__lt=today_end,
                is_deleted=False
            ).exclude(status='cancelled')

            waiting = all_today.filter(status='scheduled').count()
            in_progress = all_today.filter(status='in_progress').count()
            completed = all_today.filter(status='completed').count()

            # 금일 예약환자 5명 (시간순, 취소 제외)
            today_appointments = all_today.select_related('patient').order_by('admission_date')[:5]

            return Response({
                'today_appointments': [
                    {
                        'encounter_id': enc.id,
                        'patient_id': enc.patient.id,
                        'patient_name': enc.patient.name,
                        'patient_number': enc.patient.patient_number,
                        'appointment_time': enc.admission_date.isoformat(),
                        'scheduled_time': enc.scheduled_time.strftime('%H:%M:%S') if enc.scheduled_time else None,
                        'encounter_type': enc.encounter_type,
                        'status': enc.status,
                        'reason': enc.chief_complaint or '',
                        'department': enc.department,
                    }
                    for enc in today_appointments
                ],
                'stats': {
                    'total_today': all_today.count(),
                    'waiting': waiting,
                    'in_progress': in_progress,
                    'completed': completed,
                },
            })

        except Exception as e:
            logger.error(f"Doctor dashboard stats error: {str(e)}")
            return Response(
                {'error': '통계를 불러오는 중 오류가 발생했습니다.'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

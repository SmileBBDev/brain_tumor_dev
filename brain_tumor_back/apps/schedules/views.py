from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.pagination import PageNumberPagination
from django.utils import timezone
from datetime import timedelta
from drf_spectacular.utils import extend_schema, extend_schema_view, OpenApiParameter

from .models import DoctorSchedule
from .serializers import (
    DoctorScheduleListSerializer,
    DoctorScheduleDetailSerializer,
    DoctorScheduleCreateSerializer,
    DoctorScheduleUpdateSerializer,
    DoctorScheduleCalendarSerializer,
)


class DoctorSchedulePagination(PageNumberPagination):
    """일정 목록 페이지네이션"""
    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 100


@extend_schema_view(
    list=extend_schema(
        summary="의사 일정 목록 조회",
        description="현재 로그인한 의사의 일정 목록을 조회합니다.",
        parameters=[
            OpenApiParameter(name='schedule_type', description='일정 유형 필터', type=str),
            OpenApiParameter(name='start_date', description='시작일 (YYYY-MM-DD)', type=str),
            OpenApiParameter(name='end_date', description='종료일 (YYYY-MM-DD)', type=str),
        ]
    ),
    retrieve=extend_schema(summary="의사 일정 상세 조회"),
    create=extend_schema(summary="의사 일정 생성"),
    partial_update=extend_schema(summary="의사 일정 수정"),
    destroy=extend_schema(summary="의사 일정 삭제"),
)
class DoctorScheduleViewSet(viewsets.ModelViewSet):
    """
    의사 일정 CRUD ViewSet

    의사의 개인 일정(회의, 휴가, 교육 등)을 관리합니다.
    """
    permission_classes = [IsAuthenticated]
    pagination_class = DoctorSchedulePagination

    def get_queryset(self):
        """현재 사용자의 일정만 조회"""
        queryset = DoctorSchedule.objects.filter(
            doctor=self.request.user,
            is_deleted=False
        )

        # 일정 유형 필터
        schedule_type = self.request.query_params.get('schedule_type')
        if schedule_type:
            queryset = queryset.filter(schedule_type=schedule_type)

        # 날짜 범위 필터
        start_date = self.request.query_params.get('start_date')
        end_date = self.request.query_params.get('end_date')

        if start_date:
            queryset = queryset.filter(start_datetime__date__gte=start_date)
        if end_date:
            queryset = queryset.filter(start_datetime__date__lte=end_date)

        return queryset.order_by('start_datetime')

    def get_serializer_class(self):
        """액션별 Serializer 선택"""
        if self.action == 'list':
            return DoctorScheduleListSerializer
        elif self.action == 'create':
            return DoctorScheduleCreateSerializer
        elif self.action in ['update', 'partial_update']:
            return DoctorScheduleUpdateSerializer
        elif self.action == 'calendar':
            return DoctorScheduleCalendarSerializer
        return DoctorScheduleDetailSerializer

    def perform_destroy(self, instance):
        """Soft Delete"""
        instance.is_deleted = True
        instance.save()

    @extend_schema(
        summary="캘린더용 일정 조회",
        description="지정된 월의 일정을 캘린더 표시용 간소화된 형식으로 반환합니다.",
        parameters=[
            OpenApiParameter(name='year', description='년도 (YYYY)', type=int, required=True),
            OpenApiParameter(name='month', description='월 (1-12)', type=int, required=True),
        ]
    )
    @action(detail=False, methods=['get'])
    def calendar(self, request):
        """캘린더용 월별 일정 조회"""
        year = request.query_params.get('year')
        month = request.query_params.get('month')

        if not year or not month:
            return Response(
                {'error': 'year와 month 파라미터가 필요합니다.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            year = int(year)
            month = int(month)
        except ValueError:
            return Response(
                {'error': 'year와 month는 숫자여야 합니다.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # 해당 월의 시작/끝 계산
        start_date = timezone.datetime(year, month, 1, tzinfo=timezone.get_current_timezone())
        if month == 12:
            end_date = timezone.datetime(year + 1, 1, 1, tzinfo=timezone.get_current_timezone())
        else:
            end_date = timezone.datetime(year, month + 1, 1, tzinfo=timezone.get_current_timezone())

        # 일정 조회 (해당 월에 걸치는 모든 일정)
        schedules = DoctorSchedule.objects.filter(
            doctor=request.user,
            is_deleted=False,
            start_datetime__lt=end_date,
            end_datetime__gte=start_date
        ).order_by('start_datetime')

        serializer = DoctorScheduleCalendarSerializer(schedules, many=True)
        return Response(serializer.data)

    @extend_schema(
        summary="오늘 일정 조회",
        description="오늘의 일정을 조회합니다."
    )
    @action(detail=False, methods=['get'])
    def today(self, request):
        """오늘의 일정 조회"""
        now = timezone.now()
        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        today_end = today_start + timedelta(days=1)

        schedules = DoctorSchedule.objects.filter(
            doctor=request.user,
            is_deleted=False,
            start_datetime__lt=today_end,
            end_datetime__gte=today_start
        ).order_by('start_datetime')

        serializer = DoctorScheduleListSerializer(schedules, many=True)
        return Response(serializer.data)

    @extend_schema(
        summary="이번 주 일정 조회",
        description="이번 주의 일정을 조회합니다."
    )
    @action(detail=False, methods=['get'], url_path='this-week')
    def this_week(self, request):
        """이번 주 일정 조회"""
        now = timezone.now()
        today = now.replace(hour=0, minute=0, second=0, microsecond=0)

        # 이번 주 월요일
        week_start = today - timedelta(days=today.weekday())
        week_end = week_start + timedelta(days=7)

        schedules = DoctorSchedule.objects.filter(
            doctor=request.user,
            is_deleted=False,
            start_datetime__lt=week_end,
            end_datetime__gte=week_start
        ).order_by('start_datetime')

        serializer = DoctorScheduleListSerializer(schedules, many=True)
        return Response(serializer.data)

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.exceptions import PermissionDenied
from django.db import transaction
from django.utils import timezone
from drf_spectacular.utils import extend_schema, extend_schema_view, OpenApiParameter

from .models import OCS, OCSHistory
from .permissions import OCSPermission
from .serializers import (
    OCSListSerializer,
    OCSDetailSerializer,
    OCSCreateSerializer,
    OCSUpdateSerializer,
    OCSAcceptSerializer,
    OCSStartSerializer,
    OCSSaveResultSerializer,
    OCSSubmitResultSerializer,
    OCSConfirmSerializer,
    OCSCancelSerializer,
    OCSHistorySerializer,
)


# =============================================================================
# OCS Views - 단일 테이블 설계
# =============================================================================
# 상세 기획: ocs_제작기획.md 참조
# =============================================================================


@extend_schema_view(
    list=extend_schema(
        summary="OCS 목록 조회",
        description="OCS 목록을 조회합니다. 필터링 가능.",
        parameters=[
            OpenApiParameter(name='ocs_status', description='상태 필터', type=str),
            OpenApiParameter(name='job_role', description='작업 역할 필터', type=str),
            OpenApiParameter(name='priority', description='우선순위 필터', type=str),
            OpenApiParameter(name='patient_id', description='환자 ID 필터', type=int),
            OpenApiParameter(name='doctor_id', description='의사 ID 필터', type=int),
            OpenApiParameter(name='worker_id', description='작업자 ID 필터', type=int),
            OpenApiParameter(name='unassigned', description='미배정 OCS만 조회', type=bool),
        ]
    ),
    retrieve=extend_schema(summary="OCS 상세 조회", description="OCS 상세 정보를 조회합니다."),
    create=extend_schema(summary="OCS 생성", description="새로운 OCS를 생성합니다."),
    partial_update=extend_schema(summary="OCS 수정", description="OCS를 수정합니다."),
    destroy=extend_schema(summary="OCS 삭제", description="OCS를 삭제합니다 (Soft Delete)."),
)
class OCSViewSet(viewsets.ModelViewSet):
    """
    OCS (Order Communication System) ViewSet

    의사와 작업자 간 오더 관리를 위한 API.
    """
    permission_classes = [IsAuthenticated, OCSPermission]

    def get_queryset(self):
        """필터링된 OCS 목록 반환"""
        queryset = OCS.objects.filter(is_deleted=False).select_related(
            'patient', 'doctor', 'worker', 'encounter'
        ).prefetch_related('history')

        # 필터 적용
        params = self.request.query_params

        if params.get('ocs_status'):
            queryset = queryset.filter(ocs_status=params.get('ocs_status'))

        if params.get('job_role'):
            queryset = queryset.filter(job_role=params.get('job_role'))

        if params.get('priority'):
            queryset = queryset.filter(priority=params.get('priority'))

        if params.get('patient_id'):
            queryset = queryset.filter(patient_id=params.get('patient_id'))

        if params.get('doctor_id'):
            queryset = queryset.filter(doctor_id=params.get('doctor_id'))

        if params.get('worker_id'):
            queryset = queryset.filter(worker_id=params.get('worker_id'))

        if params.get('unassigned') == 'true':
            queryset = queryset.filter(worker__isnull=True)

        return queryset

    def get_serializer_class(self):
        """액션에 따른 Serializer 반환"""
        if self.action == 'list':
            return OCSListSerializer
        elif self.action == 'create':
            return OCSCreateSerializer
        elif self.action in ['update', 'partial_update']:
            return OCSUpdateSerializer
        return OCSDetailSerializer

    def perform_destroy(self, instance):
        """Soft Delete"""
        instance.is_deleted = True
        instance.save()

    def _get_client_ip(self, request):
        """클라이언트 IP 추출"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            return x_forwarded_for.split(',')[0].strip()
        return request.META.get('REMOTE_ADDR')

    # =========================================================================
    # 추가 조회 API
    # =========================================================================

    @extend_schema(
        summary="ocs_id로 조회",
        description="ocs_id (예: ocs_0001)로 OCS를 조회합니다.",
        parameters=[OpenApiParameter(name='ocs_id', description='OCS ID', type=str, required=True)]
    )
    @action(detail=False, methods=['get'])
    def by_ocs_id(self, request):
        """ocs_id로 조회"""
        ocs_id = request.query_params.get('ocs_id')
        if not ocs_id:
            return Response(
                {'error': 'ocs_id 파라미터가 필요합니다.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            ocs = OCS.objects.get(ocs_id=ocs_id, is_deleted=False)
            serializer = OCSDetailSerializer(ocs)
            return Response(serializer.data)
        except OCS.DoesNotExist:
            return Response(
                {'error': '해당 OCS를 찾을 수 없습니다.'},
                status=status.HTTP_404_NOT_FOUND
            )

    @extend_schema(summary="미완료 OCS 목록", description="확정되지 않은 OCS 목록을 조회합니다.")
    @action(detail=False, methods=['get'])
    def pending(self, request):
        """미완료 OCS 목록"""
        queryset = self.get_queryset().exclude(
            ocs_status__in=[OCS.OcsStatus.CONFIRMED, OCS.OcsStatus.CANCELLED]
        )
        serializer = OCSListSerializer(queryset, many=True)
        return Response(serializer.data)

    @extend_schema(summary="환자별 OCS 목록", description="특정 환자의 OCS 목록을 조회합니다.")
    @action(detail=False, methods=['get'], url_path='by_patient')
    def by_patient(self, request):
        """환자별 OCS 목록"""
        patient_id = request.query_params.get('patient_id')
        if not patient_id:
            return Response(
                {'error': 'patient_id 파라미터가 필요합니다.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        queryset = self.get_queryset().filter(patient_id=patient_id)
        serializer = OCSListSerializer(queryset, many=True)
        return Response(serializer.data)

    @extend_schema(summary="의사별 OCS 목록", description="특정 의사의 OCS 목록을 조회합니다.")
    @action(detail=False, methods=['get'], url_path='by_doctor')
    def by_doctor(self, request):
        """의사별 OCS 목록"""
        doctor_id = request.query_params.get('doctor_id')
        if not doctor_id:
            return Response(
                {'error': 'doctor_id 파라미터가 필요합니다.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        queryset = self.get_queryset().filter(doctor_id=doctor_id)
        serializer = OCSListSerializer(queryset, many=True)
        return Response(serializer.data)

    @extend_schema(summary="작업자별 OCS 목록", description="특정 작업자의 OCS 목록을 조회합니다.")
    @action(detail=False, methods=['get'], url_path='by_worker')
    def by_worker(self, request):
        """작업자별 OCS 목록"""
        worker_id = request.query_params.get('worker_id')
        if not worker_id:
            return Response(
                {'error': 'worker_id 파라미터가 필요합니다.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        queryset = self.get_queryset().filter(worker_id=worker_id)
        serializer = OCSListSerializer(queryset, many=True)
        return Response(serializer.data)

    # =========================================================================
    # 상태 변경 API
    # =========================================================================

    @extend_schema(summary="오더 접수", description="ORDERED → ACCEPTED 상태로 변경합니다.")
    @action(detail=True, methods=['post'])
    @transaction.atomic
    def accept(self, request, pk=None):
        """오더 접수 (ORDERED → ACCEPTED)"""
        ocs = OCS.objects.select_for_update().get(pk=pk, is_deleted=False)

        serializer = OCSAcceptSerializer(instance=ocs, data={}, context={'request': request})
        serializer.is_valid(raise_exception=True)

        # 상태 변경
        from_status = ocs.ocs_status
        ocs.worker = request.user
        ocs.ocs_status = OCS.OcsStatus.ACCEPTED
        ocs.accepted_at = timezone.now()
        ocs.worker_result = ocs.get_default_worker_result()
        ocs.save()

        # 이력 기록
        OCSHistory.objects.create(
            ocs=ocs,
            action=OCSHistory.Action.ACCEPTED,
            actor=request.user,
            from_status=from_status,
            to_status=ocs.ocs_status,
            to_worker=request.user,
            ip_address=self._get_client_ip(request)
        )

        return Response(OCSDetailSerializer(ocs).data)

    @extend_schema(summary="작업 시작", description="ACCEPTED → IN_PROGRESS 상태로 변경합니다.")
    @action(detail=True, methods=['post'])
    @transaction.atomic
    def start(self, request, pk=None):
        """작업 시작 (ACCEPTED → IN_PROGRESS)"""
        ocs = OCS.objects.select_for_update().get(pk=pk, is_deleted=False)

        serializer = OCSStartSerializer(instance=ocs, data={}, context={'request': request})
        serializer.is_valid(raise_exception=True)

        # 상태 변경
        from_status = ocs.ocs_status
        ocs.ocs_status = OCS.OcsStatus.IN_PROGRESS
        ocs.in_progress_at = timezone.now()
        ocs.save()

        # 이력 기록
        OCSHistory.objects.create(
            ocs=ocs,
            action=OCSHistory.Action.STARTED,
            actor=request.user,
            from_status=from_status,
            to_status=ocs.ocs_status,
            ip_address=self._get_client_ip(request)
        )

        return Response(OCSDetailSerializer(ocs).data)

    @extend_schema(summary="결과 임시 저장", description="작업 결과를 임시 저장합니다.")
    @action(detail=True, methods=['post'])
    def save_result(self, request, pk=None):
        """결과 임시 저장"""
        ocs = self.get_object()

        serializer = OCSSaveResultSerializer(
            instance=ocs,
            data=request.data,
            context={'request': request}
        )
        serializer.is_valid(raise_exception=True)

        # 결과 저장
        if 'worker_result' in request.data:
            ocs.worker_result = request.data['worker_result']
        if 'attachments' in request.data:
            ocs.attachments = request.data['attachments']
        ocs.save()

        # 이력 기록
        OCSHistory.objects.create(
            ocs=ocs,
            action=OCSHistory.Action.RESULT_SAVED,
            actor=request.user,
            ip_address=self._get_client_ip(request)
        )

        return Response(OCSDetailSerializer(ocs).data)

    @extend_schema(summary="결과 제출", description="IN_PROGRESS → RESULT_READY 상태로 변경합니다.")
    @action(detail=True, methods=['post'])
    @transaction.atomic
    def submit_result(self, request, pk=None):
        """결과 제출 (IN_PROGRESS → RESULT_READY)"""
        ocs = OCS.objects.select_for_update().get(pk=pk, is_deleted=False)

        serializer = OCSSubmitResultSerializer(
            instance=ocs,
            data=request.data,
            context={'request': request}
        )
        serializer.is_valid(raise_exception=True)

        # 결과 저장 및 상태 변경
        from_status = ocs.ocs_status
        if 'worker_result' in request.data:
            ocs.worker_result = request.data['worker_result']
        if 'attachments' in request.data:
            ocs.attachments = request.data['attachments']
        ocs.ocs_status = OCS.OcsStatus.RESULT_READY
        ocs.result_ready_at = timezone.now()
        ocs.save()

        # 이력 기록
        OCSHistory.objects.create(
            ocs=ocs,
            action=OCSHistory.Action.SUBMITTED,
            actor=request.user,
            from_status=from_status,
            to_status=ocs.ocs_status,
            ip_address=self._get_client_ip(request)
        )

        return Response(OCSDetailSerializer(ocs).data)

    @extend_schema(summary="확정", description="RESULT_READY → CONFIRMED 상태로 변경합니다.")
    @action(detail=True, methods=['post'])
    @transaction.atomic
    def confirm(self, request, pk=None):
        """확정 (RESULT_READY → CONFIRMED)"""
        ocs = OCS.objects.select_for_update().get(pk=pk, is_deleted=False)

        serializer = OCSConfirmSerializer(
            instance=ocs,
            data=request.data,
            context={'request': request}
        )
        serializer.is_valid(raise_exception=True)

        # 상태 변경
        from_status = ocs.ocs_status
        ocs.ocs_status = OCS.OcsStatus.CONFIRMED
        ocs.ocs_result = request.data.get('ocs_result')
        ocs.confirmed_at = timezone.now()

        # worker_result에 _confirmed 플래그 설정
        if isinstance(ocs.worker_result, dict):
            ocs.worker_result['_confirmed'] = True

        ocs.save()

        # 이력 기록
        OCSHistory.objects.create(
            ocs=ocs,
            action=OCSHistory.Action.CONFIRMED,
            actor=request.user,
            from_status=from_status,
            to_status=ocs.ocs_status,
            ip_address=self._get_client_ip(request)
        )

        return Response(OCSDetailSerializer(ocs).data)

    @extend_schema(summary="취소", description="OCS를 취소합니다.")
    @action(detail=True, methods=['post'])
    @transaction.atomic
    def cancel(self, request, pk=None):
        """취소"""
        ocs = OCS.objects.select_for_update().get(pk=pk, is_deleted=False)

        serializer = OCSCancelSerializer(
            instance=ocs,
            data=request.data,
            context={'request': request}
        )
        serializer.is_valid(raise_exception=True)

        from_status = ocs.ocs_status
        from_worker = ocs.worker
        cancel_reason = request.data.get('cancel_reason', '')

        # 의사 취소 vs 작업자 취소 구분
        is_doctor = ocs.doctor == request.user
        is_worker = ocs.worker == request.user

        if is_doctor:
            # 의사가 취소 = OCS 전체 취소
            ocs.ocs_status = OCS.OcsStatus.CANCELLED
            ocs.cancelled_at = timezone.now()
            ocs.cancel_reason = cancel_reason

            action_type = OCSHistory.Action.CANCELLED
            to_status = OCS.OcsStatus.CANCELLED
        else:
            # 작업자가 취소 = 작업 포기 (다른 작업자가 수락 가능)
            ocs.worker = None
            ocs.ocs_status = OCS.OcsStatus.ORDERED
            ocs.accepted_at = None
            ocs.in_progress_at = None

            action_type = OCSHistory.Action.CANCELLED
            to_status = OCS.OcsStatus.ORDERED

        ocs.save()

        # 이력 기록
        OCSHistory.objects.create(
            ocs=ocs,
            action=action_type,
            actor=request.user,
            from_status=from_status,
            to_status=to_status,
            from_worker=from_worker,
            to_worker=None if not is_doctor else from_worker,
            reason=cancel_reason,
            ip_address=self._get_client_ip(request)
        )

        return Response(OCSDetailSerializer(ocs).data)

    # =========================================================================
    # 이력 조회 API
    # =========================================================================

    @extend_schema(summary="OCS 이력 조회", description="특정 OCS의 변경 이력을 조회합니다.")
    @action(detail=True, methods=['get'])
    def history(self, request, pk=None):
        """OCS 이력 조회"""
        ocs = self.get_object()
        history = ocs.history.all()
        serializer = OCSHistorySerializer(history, many=True)
        return Response(serializer.data)

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.exceptions import PermissionDenied
from rest_framework.pagination import PageNumberPagination
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
from .notifications import notify_ocs_status_changed, notify_ocs_created, notify_ocs_cancelled


# =============================================================================
# OCS Views - 단일 테이블 설계
# =============================================================================
# 상세 기획: ocs_제작기획.md 참조
# =============================================================================


class OCSPagination(PageNumberPagination):
    """OCS 목록 페이지네이션"""
    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 100


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
    pagination_class = OCSPagination

    def get_queryset(self):
        """필터링된 OCS 목록 반환"""
        queryset = OCS.objects.filter(is_deleted=False).select_related(
            'patient', 'doctor', 'worker', 'encounter'
        )

        # 목록 조회 시 최적화: 큰 JSON 필드 제외, history prefetch 안함
        if self.action == 'list':
            # worker_result, attachments는 목록에서 필요 없음 - defer로 지연 로딩
            queryset = queryset.defer('worker_result', 'attachments', 'doctor_request')
        elif self.action == 'retrieve':
            # 상세 조회 시에만 history prefetch
            queryset = queryset.prefetch_related('history')

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

        # 검색 기능 (환자명, 환자번호, OCS ID, 작업유형)
        search_query = params.get('q') or params.get('search')
        if search_query:
            from django.db.models import Q
            queryset = queryset.filter(
                Q(patient__name__icontains=search_query) |
                Q(patient__patient_number__icontains=search_query) |
                Q(ocs_id__icontains=search_query) |
                Q(job_type__icontains=search_query)
            )

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

        # WebSocket 알림
        notify_ocs_status_changed(ocs, from_status, ocs.ocs_status, request.user)

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

        # WebSocket 알림
        notify_ocs_status_changed(ocs, from_status, ocs.ocs_status, request.user)

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

        # WebSocket 알림
        notify_ocs_status_changed(ocs, from_status, ocs.ocs_status, request.user)

        return Response(OCSDetailSerializer(ocs).data)

    @extend_schema(summary="확정", description="RESULT_READY → CONFIRMED 상태로 변경합니다. LIS의 경우 IN_PROGRESS → CONFIRMED도 가능합니다.")
    @action(detail=True, methods=['post'])
    @transaction.atomic
    def confirm(self, request, pk=None):
        """확정 (RESULT_READY → CONFIRMED 또는 LIS의 경우 IN_PROGRESS → CONFIRMED)"""
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
        ocs.ocs_result = request.data.get('ocs_result', True)
        ocs.confirmed_at = timezone.now()

        # worker_result 업데이트 (LIS에서 결과와 함께 확정하는 경우)
        if 'worker_result' in request.data:
            worker_result = request.data.get('worker_result')
            if isinstance(worker_result, dict):
                worker_result['_confirmed'] = True
                ocs.worker_result = worker_result
        elif isinstance(ocs.worker_result, dict):
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

        # WebSocket 알림
        notify_ocs_status_changed(ocs, from_status, ocs.ocs_status, request.user)

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

        # WebSocket 알림
        notify_ocs_cancelled(ocs, request.user, cancel_reason)

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

    # =========================================================================
    # 파일 업로드 API (LIS 외부 기관 데이터)
    # =========================================================================

    @extend_schema(
        summary="LIS 파일 업로드",
        description="외부 LIS/검사 장비의 Raw 데이터 파일을 업로드합니다. CSV, HL7, JSON, XML 형식을 지원합니다."
    )
    @action(detail=True, methods=['post'], url_path='upload_lis_file')
    def upload_lis_file(self, request, pk=None):
        """
        LIS 파일 업로드
        - 외부 기관 검사 결과 파일 업로드
        - attachments 필드에 파일 정보 및 외부 기관 메타데이터 저장
        """
        ocs = self.get_object()

        # LIS job_role 검증
        if ocs.job_role != 'LIS':
            return Response(
                {'error': 'LIS 오더에만 파일을 업로드할 수 있습니다.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # 파일 검증
        uploaded_file = request.FILES.get('file')
        if not uploaded_file:
            return Response(
                {'error': '파일이 필요합니다.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # 파일 확장자 검증
        allowed_extensions = ['.csv', '.hl7', '.json', '.xml']
        file_ext = '.' + uploaded_file.name.split('.')[-1].lower()
        if file_ext not in allowed_extensions:
            return Response(
                {'error': f'지원하지 않는 파일 형식입니다. (지원: {", ".join(allowed_extensions)})'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # 파일 크기 검증 (10MB)
        max_size = 10 * 1024 * 1024
        if uploaded_file.size > max_size:
            return Response(
                {'error': '파일 크기가 10MB를 초과합니다.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # 외부 기관 정보 파싱 (선택적)
        external_source = {
            "institution": {
                "name": request.data.get('institution_name') or None,
                "code": request.data.get('institution_code') or None,
                "contact": request.data.get('institution_contact') or None,
                "address": request.data.get('institution_address') or None,
            },
            "execution": {
                "performed_date": request.data.get('performed_date') or None,
                "performed_by": request.data.get('performed_by') or None,
                "specimen_collected_date": request.data.get('specimen_collected_date') or None,
                "specimen_type": request.data.get('specimen_type') or None,
            },
            "quality": {
                "lab_certification_number": request.data.get('lab_certification_number') or None,
                "qc_status": request.data.get('qc_status') or None,
                "is_verified": request.data.get('is_verified', 'false').lower() == 'true',
            },
        }

        # TODO: 실제 파일 저장 로직 (S3, 로컬 등)
        # 현재는 파일 정보만 기록
        file_info = {
            "name": uploaded_file.name,
            "size": uploaded_file.size,
            "content_type": uploaded_file.content_type,
            "uploaded_at": timezone.now().isoformat(),
            "uploaded_by": request.user.id,
        }

        # attachments 업데이트
        attachments = ocs.attachments or {}
        if not isinstance(attachments, dict):
            attachments = {}

        # files 배열에 추가
        if 'files' not in attachments:
            attachments['files'] = []
        attachments['files'].append(file_info)

        # 외부 기관 정보 저장
        attachments['external_source'] = external_source
        attachments['total_size'] = sum(f.get('size', 0) for f in attachments.get('files', []))
        attachments['last_modified'] = timezone.now().isoformat()

        ocs.attachments = attachments
        ocs.save(update_fields=['attachments', 'updated_at'])

        # 이력 기록
        OCSHistory.objects.create(
            ocs=ocs,
            action=OCSHistory.Action.RESULT_SAVED,
            actor=request.user,
            reason=f'LIS 파일 업로드: {uploaded_file.name}',
            ip_address=self._get_client_ip(request)
        )

        return Response({
            'message': '파일이 성공적으로 업로드되었습니다.',
            'file': file_info,
            'external_source': external_source,
            'ocs': OCSDetailSerializer(ocs).data
        })

    # =========================================================================
    # 외부 기관 LIS 데이터 생성 API
    # =========================================================================

    @extend_schema(
        summary="외부 기관 LIS 데이터 생성",
        description="외부 기관에서 수신한 검사 결과를 새 OCS로 등록합니다. OCS ID는 extr_0001 형식으로 자동 생성됩니다."
    )
    @action(detail=False, methods=['post'], url_path='create_external_lis')
    @transaction.atomic
    def create_external_lis(self, request):
        """
        외부 기관 LIS 데이터 생성
        - 외부 기관 검사 결과를 새 OCS로 등록
        - OCS ID: extr_0001 형식
        - 파일 업로드 + 외부 기관 메타데이터 저장
        """
        from apps.patients.models import Patient

        # 필수 파라미터 검증
        patient_id = request.data.get('patient_id')
        if not patient_id:
            return Response(
                {'error': 'patient_id가 필요합니다.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            patient = Patient.objects.get(id=patient_id, is_deleted=False)
        except Patient.DoesNotExist:
            return Response(
                {'error': '환자를 찾을 수 없습니다.'},
                status=status.HTTP_404_NOT_FOUND
            )

        # 파일 검증 (선택사항 - 파일 없이도 외부 검사 등록 가능)
        uploaded_file = request.FILES.get('file')
        if uploaded_file:
            # 파일 확장자 검증
            allowed_extensions = ['.csv', '.hl7', '.json', '.xml']
            file_ext = '.' + uploaded_file.name.split('.')[-1].lower()
            if file_ext not in allowed_extensions:
                return Response(
                    {'error': f'지원하지 않는 파일 형식입니다. (지원: {", ".join(allowed_extensions)})'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # 파일 크기 검증 (10MB)
            max_size = 10 * 1024 * 1024
            if uploaded_file.size > max_size:
                return Response(
                    {'error': '파일 크기가 10MB를 초과합니다.'},
                    status=status.HTTP_400_BAD_REQUEST
                )

        # 외부용 OCS ID 생성 (extr_0001 형식)
        external_ocs_id = self._generate_external_ocs_id()

        # job_type 결정 (기본값 또는 파라미터)
        job_type = request.data.get('job_type', 'EXTERNAL')

        # 외부 기관 정보 파싱
        external_source = {
            "institution": {
                "name": request.data.get('institution_name') or None,
                "code": request.data.get('institution_code') or None,
                "contact": request.data.get('institution_contact') or None,
                "address": request.data.get('institution_address') or None,
            },
            "execution": {
                "performed_date": request.data.get('performed_date') or None,
                "performed_by": request.data.get('performed_by') or None,
                "specimen_collected_date": request.data.get('specimen_collected_date') or None,
                "specimen_type": request.data.get('specimen_type') or None,
            },
            "quality": {
                "lab_certification_number": request.data.get('lab_certification_number') or None,
                "qc_status": request.data.get('qc_status') or None,
                "is_verified": request.data.get('is_verified', 'false').lower() == 'true',
            },
        }

        # 파일 정보 (파일이 있는 경우에만)
        file_info = None
        if uploaded_file:
            file_info = {
                "name": uploaded_file.name,
                "size": uploaded_file.size,
                "content_type": uploaded_file.content_type,
                "uploaded_at": timezone.now().isoformat(),
                "uploaded_by": request.user.id,
            }

        # attachments 구성
        attachments = {
            "files": [file_info] if file_info else [],
            "external_source": external_source,
            "total_size": uploaded_file.size if uploaded_file else 0,
            "last_modified": timezone.now().isoformat(),
            "_custom": {}
        }

        # OCS 생성
        ocs = OCS.objects.create(
            ocs_id=external_ocs_id,
            patient=patient,
            doctor=request.user,  # 업로드한 사용자를 doctor로 설정
            worker=request.user,  # 외부 데이터는 업로드한 사용자가 작업자
            job_role='LIS',
            job_type=job_type,
            ocs_status=OCS.OcsStatus.RESULT_READY,  # 외부 데이터는 바로 결과 대기 상태
            priority=request.data.get('priority', OCS.Priority.NORMAL),
            attachments=attachments,
            worker_result={
                "_template": "LIS",
                "_version": "1.0",
                "_confirmed": False,
                "_external": True,  # 외부 데이터 표시
                "test_results": [],
                "summary": request.data.get('summary', ''),
                "interpretation": request.data.get('interpretation', ''),
                "_custom": {}
            },
            doctor_request={
                "_template": "external",
                "_version": "1.0",
                "source": "external_upload",
                "original_filename": uploaded_file.name if uploaded_file else None,
                "_custom": {}
            },
            accepted_at=timezone.now(),
            in_progress_at=timezone.now(),
            result_ready_at=timezone.now(),
        )

        # 이력 기록
        history_reason = f'외부 기관 LIS 데이터 업로드: {uploaded_file.name}' if uploaded_file else '외부 기관 LIS 데이터 등록 (파일 없음)'
        OCSHistory.objects.create(
            ocs=ocs,
            action=OCSHistory.Action.CREATED,
            actor=request.user,
            to_status=OCS.OcsStatus.RESULT_READY,
            reason=history_reason,
            ip_address=self._get_client_ip(request)
        )

        return Response({
            'message': '외부 기관 검사 결과가 등록되었습니다.',
            'ocs_id': external_ocs_id,
            'file': file_info,
            'external_source': external_source,
            'ocs': OCSDetailSerializer(ocs).data
        }, status=status.HTTP_201_CREATED)

    def _generate_external_ocs_id(self):
        """외부 데이터용 OCS ID 생성 (extr_0001 형식)"""
        last_external = OCS.objects.filter(
            ocs_id__startswith='extr_'
        ).order_by('-ocs_id').first()

        if last_external and last_external.ocs_id:
            try:
                last_num = int(last_external.ocs_id.split('_')[1])
                return f"extr_{last_num + 1:04d}"
            except (ValueError, IndexError):
                pass
        return "extr_0001"

    def _generate_external_ris_id(self):
        """외부 RIS 데이터용 OCS ID 생성 (risx_0001 형식)"""
        last_external = OCS.objects.filter(
            ocs_id__startswith='risx_'
        ).order_by('-ocs_id').first()

        if last_external and last_external.ocs_id:
            try:
                last_num = int(last_external.ocs_id.split('_')[1])
                return f"risx_{last_num + 1:04d}"
            except (ValueError, IndexError):
                pass
        return "risx_0001"

    # =========================================================================
    # RIS 파일 업로드 API (외부 영상 데이터)
    # =========================================================================

    @extend_schema(
        summary="RIS 파일 업로드",
        description="외부 RIS/PACS의 영상 데이터 파일을 업로드합니다. DICOM, JPEG, PNG, PDF, ZIP 형식을 지원합니다."
    )
    @action(detail=True, methods=['post'], url_path='upload_ris_file')
    def upload_ris_file(self, request, pk=None):
        """
        RIS 파일 업로드
        - 외부 기관 영상 결과 파일 업로드
        - attachments 필드에 파일 정보 및 외부 기관 메타데이터 저장
        """
        ocs = self.get_object()

        # RIS job_role 검증
        if ocs.job_role != 'RIS':
            return Response(
                {'error': 'RIS 오더에만 파일을 업로드할 수 있습니다.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # 파일 검증
        uploaded_file = request.FILES.get('file')
        if not uploaded_file:
            return Response(
                {'error': '파일이 필요합니다.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # 파일 확장자 검증
        allowed_extensions = ['.dcm', '.dicom', '.jpg', '.jpeg', '.png', '.pdf', '.zip']
        file_ext = '.' + uploaded_file.name.split('.')[-1].lower()
        if file_ext not in allowed_extensions:
            return Response(
                {'error': f'지원하지 않는 파일 형식입니다. (지원: {", ".join(allowed_extensions)})'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # 파일 크기 검증 (100MB)
        max_size = 100 * 1024 * 1024
        if uploaded_file.size > max_size:
            return Response(
                {'error': '파일 크기가 100MB를 초과합니다.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # 외부 기관 정보 파싱 (선택적)
        external_source = {
            "institution": {
                "name": request.data.get('institution_name') or None,
                "code": request.data.get('institution_code') or None,
                "contact": request.data.get('institution_contact') or None,
                "address": request.data.get('institution_address') or None,
            },
            "execution": {
                "performed_date": request.data.get('performed_date') or None,
                "performed_by": request.data.get('performed_by') or None,
                "modality": request.data.get('modality') or None,
                "body_part": request.data.get('body_part') or None,
            },
            "quality": {
                "equipment_certification_number": request.data.get('equipment_certification_number') or None,
                "qc_status": request.data.get('qc_status') or None,
                "is_verified": request.data.get('is_verified', 'false').lower() == 'true',
            },
        }

        # TODO: 실제 파일 저장 로직 (S3, 로컬 등)
        file_info = {
            "name": uploaded_file.name,
            "size": uploaded_file.size,
            "content_type": uploaded_file.content_type,
            "uploaded_at": timezone.now().isoformat(),
            "uploaded_by": request.user.id,
        }

        # attachments 업데이트
        attachments = ocs.attachments or {}
        if not isinstance(attachments, dict):
            attachments = {}

        if 'files' not in attachments:
            attachments['files'] = []
        attachments['files'].append(file_info)

        attachments['external_source'] = external_source
        attachments['total_size'] = sum(f.get('size', 0) for f in attachments.get('files', []))
        attachments['last_modified'] = timezone.now().isoformat()

        ocs.attachments = attachments
        ocs.save(update_fields=['attachments', 'updated_at'])

        # 이력 기록
        OCSHistory.objects.create(
            ocs=ocs,
            action=OCSHistory.Action.RESULT_SAVED,
            actor=request.user,
            reason=f'RIS 파일 업로드: {uploaded_file.name}',
            ip_address=self._get_client_ip(request)
        )

        return Response({
            'message': '파일이 성공적으로 업로드되었습니다.',
            'file': file_info,
            'external_source': external_source,
            'ocs': OCSDetailSerializer(ocs).data
        })

    @extend_schema(
        summary="외부 기관 RIS 데이터 생성",
        description="외부 기관에서 수신한 영상 결과를 새 OCS로 등록합니다. OCS ID는 risx_0001 형식으로 자동 생성됩니다."
    )
    @action(detail=False, methods=['post'], url_path='create_external_ris')
    @transaction.atomic
    def create_external_ris(self, request):
        """
        외부 기관 RIS 데이터 생성
        - 외부 기관 영상 결과를 새 OCS로 등록
        - OCS ID: risx_0001 형식
        - 파일 업로드 + 외부 기관 메타데이터 저장
        """
        from apps.patients.models import Patient

        # 필수 파라미터 검증
        patient_id = request.data.get('patient_id')
        if not patient_id:
            return Response(
                {'error': 'patient_id가 필요합니다.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            patient = Patient.objects.get(id=patient_id, is_deleted=False)
        except Patient.DoesNotExist:
            return Response(
                {'error': '환자를 찾을 수 없습니다.'},
                status=status.HTTP_404_NOT_FOUND
            )

        # 파일 검증 (선택사항 - 파일 없이도 외부 영상 등록 가능)
        uploaded_file = request.FILES.get('file')
        if uploaded_file:
            # 파일 확장자 검증
            allowed_extensions = ['.dcm', '.dicom', '.jpg', '.jpeg', '.png', '.pdf', '.zip']
            file_ext = '.' + uploaded_file.name.split('.')[-1].lower()
            if file_ext not in allowed_extensions:
                return Response(
                    {'error': f'지원하지 않는 파일 형식입니다. (지원: {", ".join(allowed_extensions)})'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # 파일 크기 검증 (100MB)
            max_size = 100 * 1024 * 1024
            if uploaded_file.size > max_size:
                return Response(
                    {'error': '파일 크기가 100MB를 초과합니다.'},
                    status=status.HTTP_400_BAD_REQUEST
                )

        # 외부용 RIS OCS ID 생성 (risx_0001 형식)
        external_ocs_id = self._generate_external_ris_id()

        # job_type 결정
        job_type = request.data.get('job_type', 'CT')

        # 외부 기관 정보 파싱
        external_source = {
            "institution": {
                "name": request.data.get('institution_name') or None,
                "code": request.data.get('institution_code') or None,
                "contact": request.data.get('institution_contact') or None,
                "address": request.data.get('institution_address') or None,
            },
            "execution": {
                "performed_date": request.data.get('performed_date') or None,
                "performed_by": request.data.get('performed_by') or None,
                "modality": request.data.get('modality') or None,
                "body_part": request.data.get('body_part') or None,
            },
            "quality": {
                "equipment_certification_number": request.data.get('equipment_certification_number') or None,
                "qc_status": request.data.get('qc_status') or None,
                "is_verified": request.data.get('is_verified', 'false').lower() == 'true',
            },
        }

        # 파일 정보 (파일이 있는 경우에만)
        file_info = None
        if uploaded_file:
            file_info = {
                "name": uploaded_file.name,
                "size": uploaded_file.size,
                "content_type": uploaded_file.content_type,
                "uploaded_at": timezone.now().isoformat(),
                "uploaded_by": request.user.id,
            }

        # attachments 구성
        attachments = {
            "files": [file_info] if file_info else [],
            "external_source": external_source,
            "total_size": uploaded_file.size if uploaded_file else 0,
            "last_modified": timezone.now().isoformat(),
            "_custom": {}
        }

        # OCS 생성
        ocs = OCS.objects.create(
            ocs_id=external_ocs_id,
            patient=patient,
            doctor=request.user,
            worker=request.user,
            job_role='RIS',
            job_type=job_type,
            ocs_status=OCS.OcsStatus.RESULT_READY,
            priority=request.data.get('priority', OCS.Priority.NORMAL),
            attachments=attachments,
            worker_result={
                "_template": "RIS",
                "_version": "1.0",
                "_confirmed": False,
                "_external": True,
                "findings": [],
                "summary": request.data.get('summary', ''),
                "interpretation": request.data.get('interpretation', ''),
                "_custom": {}
            },
            doctor_request={
                "_template": "external",
                "_version": "1.0",
                "source": "external_upload",
                "original_filename": uploaded_file.name if uploaded_file else None,
                "_custom": {}
            },
            accepted_at=timezone.now(),
            in_progress_at=timezone.now(),
            result_ready_at=timezone.now(),
        )

        # 이력 기록
        history_reason = f'외부 기관 RIS 데이터 업로드: {uploaded_file.name}' if uploaded_file else '외부 기관 RIS 데이터 등록 (파일 없음)'
        OCSHistory.objects.create(
            ocs=ocs,
            action=OCSHistory.Action.CREATED,
            actor=request.user,
            to_status=OCS.OcsStatus.RESULT_READY,
            reason=history_reason,
            ip_address=self._get_client_ip(request)
        )

        return Response({
            'message': '외부 기관 영상 결과가 등록되었습니다.',
            'ocs_id': external_ocs_id,
            'file': file_info,
            'external_source': external_source,
            'ocs': OCSDetailSerializer(ocs).data
        }, status=status.HTTP_201_CREATED)

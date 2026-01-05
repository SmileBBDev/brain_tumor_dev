"""
EMR ViewSets for CRUD Operations

아키텍처:
- Single Source of Truth: OpenEMR (FHIR Server)
- Django DB: Read Cache Only
- Write-Through Strategy: FHIR 서버 먼저 업데이트 → 성공 시 Django DB 업데이트
"""

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from django.utils import timezone
import logging

from .models import PatientCache, Encounter, Order, OrderItem
from .serializers import (
    PatientCacheSerializer, PatientCreateSerializer,
    EncounterSerializer, EncounterCreateSerializer,
    OrderSerializer, OrderCreateSerializer,
    OrderItemSerializer, OrderItemUpdateSerializer
)
from .business_services import PatientService, EncounterService, OrderService
from .services.openemr_client import OpenEMRClient
from .services.openemr_mapper import openemr_patient_to_dict
from .fhir_adapter import FHIRServiceAdapter
from drf_spectacular.utils import extend_schema, extend_schema_view, OpenApiParameter, OpenApiExample

logger = logging.getLogger(__name__)


from .utils import ByPatientMixin

@extend_schema_view(
    list=extend_schema(summary="환자 목록 조회", tags=['emr']),
    retrieve=extend_schema(summary="환자 상세 조회", tags=['emr']),
    create=extend_schema(
        summary="환자 생성",
        description="새로운 환자를 생성하고 OpenEMR과 동기화합니다.",
        tags=['emr'],
        responses={201: PatientCacheSerializer}
    ),
    partial_update=extend_schema(summary="환자 정보 부분 수정", tags=['emr']),
    update=extend_schema(summary="환자 정보 전체 수정", tags=['emr']),
    destroy=extend_schema(summary="환자 삭제", tags=['emr']),
    search=extend_schema(summary="환자 검색", tags=['emr']),
)
class PatientCacheViewSet(viewsets.ModelViewSet):
    """
    환자 CRUD ViewSet (Write-Through Pattern)
    """
    queryset = PatientCache.objects.all()
    permission_classes = [AllowAny]  # 개발 모드

    def get_serializer_class(self):
        if self.action == 'create':
            return PatientCreateSerializer
        return PatientCacheSerializer

    def retrieve(self, request, *args, **kwargs):
        """
        환자 상세 조회 (Django MySQL 기본 정보 + OpenEMR 상세 정보)

        Returns:
            - data: Django MySQL의 기본 정보 (PatientCache)
            - openemr_detail: OpenEMR의 상세 정보 (선택적)
        """
        # Django MySQL에서 기본 정보 조회
        patient = self.get_object()
        serializer = self.get_serializer(patient)

        response_data = {
            'data': serializer.data,
            'openemr_detail': None,
        }

        # OpenEMR ID가 있으면 상세 정보 조회
        if patient.openemr_patient_id:
            try:
                openemr_client = OpenEMRClient()
                openemr_patient = openemr_client.get_patient(patient.openemr_patient_id)

                if openemr_patient:
                    # FHIR Patient 리소스 → 딕셔너리 변환
                    openemr_detail = openemr_patient_to_dict(openemr_patient)
                    response_data['openemr_detail'] = openemr_detail
                    logger.info(f"✓ Retrieved OpenEMR detail for patient {patient.patient_id}")
                else:
                    logger.warning(f"OpenEMR Patient {patient.openemr_patient_id} not found")

            except Exception as e:
                # OpenEMR 조회 실패 시 기본 정보만 반환
                logger.error(f"Failed to retrieve OpenEMR detail for patient {patient.patient_id}: {str(e)}")

        return Response(response_data)

    def create(self, request, *args, **kwargs):
        """환자 생성 (Service 레이어 사용)"""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            # Service 레이어에서 ID 자동 생성
            patient, status_dict = PatientService.create_patient(serializer.validated_data)

            # 응답용 Serializer
            response_serializer = PatientCacheSerializer(patient)
            return Response({
                "data": response_serializer.data,
                "persistence_status": status_dict
            }, status=status.HTTP_201_CREATED)
        except Exception as e:
            logger.error(f"Create failed: {str(e)}")
            return Response(
                {"error": str(e)}, 
                status=status.HTTP_400_BAD_REQUEST
            )

    @action(detail=False, methods=['get'])
    def search(self, request):
        """환자 검색 (이름, 전화번호, 이메일)"""
        query = request.query_params.get('q', '')

        queryset = self.queryset.filter(
            family_name__icontains=query
        ) | self.queryset.filter(
            given_name__icontains=query
        ) | self.queryset.filter(
            phone__icontains=query
        ) | self.queryset.filter(
            email__icontains=query
        )

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    def update(self, request, *args, **kwargs):
        """환자 정보 수정 (Service 레이어 사용 - Outbox Pattern)"""
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        
        # Serializer 검증
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        
        # Service 레이어 위임 (Outbox 자동 생성)
        # Note: optimistic locking version check is inside Service
        try:
            # Service expects 'version' in data for optimistic locking if needed
            # Here we just pass validated_data. 
            # If Client provided 'version', it should be in validated_data if field exists, or request.data
            
            update_data = serializer.validated_data.copy()
            if 'version' in request.data:
                update_data['version'] = request.data['version']
                
            updated_patient = PatientService.update_patient(
                instance.patient_id, 
                update_data
            )
            
            # Response
            new_serializer = self.get_serializer(updated_patient)
            return Response(new_serializer.data)
            
        except Exception as e:
            logger.error(f"Update failed: {str(e)}")
            return Response(
                {"error": str(e)}, 
                status=status.HTTP_400_BAD_REQUEST
            )

    def partial_update(self, request, *args, **kwargs):
        """환자 정보 부분 수정 (update 메서드 위임)"""
        kwargs['partial'] = True
        return self.update(request, *args, **kwargs)


@extend_schema_view(
    list=extend_schema(summary="진료 기록 목록 조회", tags=['emr']),
    retrieve=extend_schema(summary="진료 기록 상세 조회", tags=['emr']),
    create=extend_schema(
        summary="진료 기록 생성",
        description="새로운 진료 기록을 생성하고 OpenEMR과 동기화합니다.",
        tags=['emr'],
        responses={201: EncounterSerializer}
    ),
    by_patient=extend_schema(summary="환자별 진료 기록 조회", tags=['emr']),
)
class EncounterViewSet(ByPatientMixin, viewsets.ModelViewSet):
    """
    진료 기록 CRUD ViewSet
    """
    queryset = Encounter.objects.select_related('patient').prefetch_related('diagnoses').all()
    permission_classes = [AllowAny]  # 개발 모드

    def get_serializer_class(self):
        if self.action == 'create':
            return EncounterCreateSerializer
        return EncounterSerializer

    def create(self, request, *args, **kwargs):
        """진료 기록 생성 (Service 레이어 사용)"""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        # Service 레이어에서 ID 자동 생성
        encounter, status = EncounterService.create_encounter(serializer.validated_data)

        # 응답용 Serializer
        response_serializer = EncounterSerializer(encounter)
        return Response({
            "data": response_serializer.data,
            "persistence_status": status
        }, status=status.HTTP_201_CREATED)


@extend_schema_view(
    list=extend_schema(summary="처방 목록 조회", tags=['emr']),
    retrieve=extend_schema(summary="처방 상세 조회", tags=['emr']),
    create=extend_schema(
        summary="처방 생성",
        description="새로운 처방을 생성하고 OpenEMR과 동기화합니다.",
        tags=['emr'],
        responses={201: OrderSerializer}
    ),
    by_patient=extend_schema(summary="환자별 처방 목록 조회", tags=['emr']),
    execute=extend_schema(summary="처방 실행 (Locking 적용)", tags=['emr']),
)
class OrderViewSet(ByPatientMixin, viewsets.ModelViewSet):
    """
    처방 CRUD ViewSet
    """
    queryset = Order.objects.select_related('patient', 'encounter').prefetch_related('items').all()
    permission_classes = [AllowAny]  # 개발 모드

    def get_serializer_class(self):
        if self.action == 'create':
            return OrderCreateSerializer
        return OrderSerializer

    def create(self, request, *args, **kwargs):
        """처방 생성 (Service 레이어 사용)"""
        try:
            serializer = self.get_serializer(data=request.data)
            serializer.is_valid(raise_exception=True)

            order_data = serializer.validated_data
            items_data = order_data.pop('order_items', [])

            # Service 레이어에서 ID 자동 생성
            order, status_dict = OrderService.create_order(order_data, items_data)

            # 응답용 Serializer
            response_serializer = OrderSerializer(order)
            return Response({
                "data": response_serializer.data,
                "persistence_status": status_dict
            }, status=status.HTTP_201_CREATED)
        except Exception as e:
            logger.error(f"Order Create failed: {str(e)}")
            import traceback
            traceback.print_exc()
            return Response(
                {"error": str(e)}, 
                status=status.HTTP_400_BAD_REQUEST
            )

    @action(detail=True, methods=['post'])
    def execute(self, request, pk=None):
        """처방 실행 (Service 레이어 및 Locking 적용)"""
        order = self.get_object()
        executed_by = request.data.get('executed_by')
        current_version = request.data.get('version')  # 클라이언트가 보낸 버전

        if not executed_by:
            return Response(
                {"error": "executed_by is required"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if current_version is None:
             return Response(
                {"error": "version is required for optimistic locking"},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            updated_order = OrderService.execute_order(order.order_id, executed_by, current_version)
            serializer = self.get_serializer(updated_order)
            return Response(serializer.data)
        except Exception as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_409_CONFLICT
            )


@extend_schema_view(
    update=extend_schema(summary="처방 항목 수정", tags=['emr']),
    partial_update=extend_schema(summary="처방 항목 부분 수정", tags=['emr']),
    destroy=extend_schema(summary="처방 항목 삭제", tags=['emr']),
)
class OrderItemViewSet(viewsets.ModelViewSet):
    """
    처방 항목(상세) CRUD ViewSet
    """
    queryset = OrderItem.objects.select_related('order').all()
    permission_classes = [AllowAny]
    
    def get_serializer_class(self):
        if self.action in ['update', 'partial_update']:
            return OrderItemUpdateSerializer
        return OrderItemSerializer

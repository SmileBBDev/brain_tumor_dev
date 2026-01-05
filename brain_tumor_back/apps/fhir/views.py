"""
FHIR Views

FHIR 리소스 조회 및 동기화 API
"""
from rest_framework import status, viewsets
from rest_framework.decorators import api_view, action, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiExample
from django.shortcuts import get_object_or_404

from .models import FHIRResourceMap, FHIRSyncQueue
from .serializers import (
    FHIRResourceMapSerializer,
    FHIRSyncQueueSerializer,
    FHIRSyncRequestSerializer
)
from .converters import (
    PatientConverter,
    EncounterConverter,
    ObservationConverter,
    DiagnosticReportConverter
)
from .converters_extended import (
    MedicationRequestConverter,
    ServiceRequestConverter,
    ConditionConverter,
    ImagingStudyConverter,
    ProcedureConverter
)
from apps.emr.models import PatientCache, Encounter, EncounterDiagnosis, Order
from apps.lis.models import LabResult
# from ai.models import AIJob
from apps.ris.models import RadiologyOrder, RadiologyStudy


class FHIRResourceMapViewSet(viewsets.ReadOnlyModelViewSet):
    """
    FHIR Resource Map ViewSet (읽기 전용)

    CDSS ID ↔ FHIR ID 매핑 조회
    """
    queryset = FHIRResourceMap.objects.all()
    serializer_class = FHIRResourceMapSerializer
    permission_classes = [AllowAny]

    @extend_schema(
        summary="FHIR Resource Map 목록 조회",
        description="CDSS와 FHIR 서버 간 리소스 매핑 목록을 조회합니다.",
        tags=["FHIR"]
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    @extend_schema(
        summary="FHIR Resource Map 상세 조회",
        description="특정 FHIR 리소스 매핑 정보를 조회합니다.",
        tags=["FHIR"]
    )
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)


class FHIRSyncQueueViewSet(viewsets.ReadOnlyModelViewSet):
    """
    FHIR Sync Queue ViewSet (읽기 전용)

    FHIR 동기화 작업 큐 조회
    """
    queryset = FHIRSyncQueue.objects.select_related('resource_map').all()
    serializer_class = FHIRSyncQueueSerializer
    permission_classes = [AllowAny]

    @extend_schema(
        summary="FHIR 동기화 큐 목록 조회",
        description="FHIR 동기화 작업 큐 목록을 조회합니다.",
        tags=["FHIR"]
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    @extend_schema(
        summary="FHIR 동기화 큐 상세 조회",
        description="특정 FHIR 동기화 작업 정보를 조회합니다.",
        tags=["FHIR"]
    )
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)


@extend_schema(
    request=None,
    responses={200: dict},
    summary="FHIR Patient 리소스 조회",
    description="환자 정보를 FHIR R4 Patient 리소스 형식으로 조회합니다.",
    tags=["FHIR"],
    parameters=[
        OpenApiParameter(
            name='patient_id',
            type=str,
            location=OpenApiParameter.PATH,
            description='환자 ID (예: P-2025-000001)'
        )
    ]
)
@api_view(['GET'])
def get_patient_fhir(request, patient_id):
    """
    FHIR Patient 리소스 조회

    환자 정보를 FHIR R4 Patient 리소스 형식으로 반환합니다.
    """
    try:
        patient = get_object_or_404(PatientCache, patient_id=patient_id)
        fhir_resource = PatientConverter.to_fhir(patient)
        return Response(fhir_resource, status=status.HTTP_200_OK)
    except Exception as e:
        return Response(
            {"error": str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@extend_schema(
    request=None,
    responses={200: dict},
    summary="FHIR Encounter 리소스 조회",
    description="진료 정보를 FHIR R4 Encounter 리소스 형식으로 조회합니다.",
    tags=["FHIR"],
    parameters=[
        OpenApiParameter(
            name='encounter_id',
            type=str,
            location=OpenApiParameter.PATH,
            description='진료 ID (예: E-2025-000001)'
        )
    ]
)
@api_view(['GET'])
def get_encounter_fhir(request, encounter_id):
    """
    FHIR Encounter 리소스 조회

    진료 정보를 FHIR R4 Encounter 리소스 형식으로 반환합니다.
    """
    try:
        encounter = get_object_or_404(Encounter, encounter_id=encounter_id)
        fhir_resource = EncounterConverter.to_fhir(encounter)
        return Response(fhir_resource, status=status.HTTP_200_OK)
    except Exception as e:
        return Response(
            {"error": str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@extend_schema(
    request=None,
    responses={200: dict},
    summary="FHIR Observation 리소스 조회",
    description="검사 결과를 FHIR R4 Observation 리소스 형식으로 조회합니다.",
    tags=["FHIR"],
    parameters=[
        OpenApiParameter(
            name='result_id',
            type=str,
            location=OpenApiParameter.PATH,
            description='검사 결과 ID (예: LR-2025-000001)'
        )
    ]
)
@api_view(['GET'])
def get_observation_fhir(request, result_id):
    """
    FHIR Observation 리소스 조회

    검사 결과를 FHIR R4 Observation 리소스 형식으로 반환합니다.
    """
    try:
        lab_result = get_object_or_404(LabResult, result_id=result_id)
        fhir_resource = ObservationConverter.to_fhir(lab_result)
        return Response(fhir_resource, status=status.HTTP_200_OK)
    except Exception as e:
        return Response(
            {"error": str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@extend_schema(
    request=None,
    responses={200: dict},
    summary="FHIR DiagnosticReport 리소스 조회",
    description="AI 분석 결과를 FHIR R4 DiagnosticReport 리소스 형식으로 조회합니다.",
    tags=["FHIR"],
    parameters=[
        OpenApiParameter(
            name='job_id',
            type=int,
            location=OpenApiParameter.PATH,
            description='AI Job ID'
        )
    ]
)
@api_view(['GET'])
def get_diagnostic_report_fhir(request, job_id):
    """
    FHIR DiagnosticReport 리소스 조회

    AI 분석 결과를 FHIR R4 DiagnosticReport 리소스 형식으로 반환합니다.
    """
    try:
        ai_job = get_object_or_404(AIJob, job_id=job_id)
        fhir_resource = DiagnosticReportConverter.to_fhir(ai_job)
        return Response(fhir_resource, status=status.HTTP_200_OK)
    except Exception as e:
        return Response(
            {"error": str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@extend_schema(
    request=None,
    responses={200: dict},
    summary="FHIR MedicationRequest 리소스 조회",
    description="약물 처방 정보를 FHIR R4 MedicationRequest 리소스 형식으로 조회합니다.",
    tags=["FHIR"],
    parameters=[
        OpenApiParameter(
            name='order_id',
            type=str,
            location=OpenApiParameter.PATH,
            description='처방 ID (예: O-2025-000001)'
        )
    ]
)
@api_view(['GET'])
def get_medication_request_fhir(request, order_id):
    """
    FHIR MedicationRequest 리소스 조회

    약물 처방 정보를 FHIR R4 MedicationRequest 리소스 형식으로 반환합니다.
    """
    try:
        order = get_object_or_404(Order, order_id=order_id, order_type='medication')
        fhir_resource = MedicationRequestConverter.to_fhir(order)
        return Response(fhir_resource, status=status.HTTP_200_OK)
    except Exception as e:
        return Response(
            {"error": str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@extend_schema(
    request=None,
    responses={200: dict},
    summary="FHIR ServiceRequest 리소스 조회",
    description="검사/시술 요청 정보를 FHIR R4 ServiceRequest 리소스 형식으로 조회합니다.",
    tags=["FHIR"],
    parameters=[
        OpenApiParameter(
            name='order_id',
            type=str,
            location=OpenApiParameter.PATH,
            description='Order ID 또는 RadiologyOrder ID'
        )
    ]
)
@api_view(['GET'])
def get_service_request_fhir(request, order_id):
    """
    FHIR ServiceRequest 리소스 조회

    검사/시술 요청을 FHIR R4 ServiceRequest 리소스 형식으로 반환합니다.
    """
    try:
        # RadiologyOrder 먼저 시도
        try:
            radiology_order = RadiologyOrder.objects.get(order_id=order_id)
            fhir_resource = ServiceRequestConverter.to_fhir(radiology_order)
            return Response(fhir_resource, status=status.HTTP_200_OK)
        except RadiologyOrder.DoesNotExist:
            # 일반 Order 시도 (lab, procedure)
            order = get_object_or_404(Order, order_id=order_id)
            if order.order_type in ['lab', 'procedure', 'radiology']:
                fhir_resource = ServiceRequestConverter.to_fhir(order)
                return Response(fhir_resource, status=status.HTTP_200_OK)
            else:
                return Response(
                    {"error": "Order type not supported for ServiceRequest"},
                    status=status.HTTP_400_BAD_REQUEST
                )
    except Exception as e:
        return Response(
            {"error": str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@extend_schema(
    request=None,
    responses={200: dict},
    summary="FHIR Condition 리소스 조회",
    description="진단 정보를 FHIR R4 Condition 리소스 형식으로 조회합니다.",
    tags=["FHIR"],
    parameters=[
        OpenApiParameter(
            name='diagnosis_id',
            type=int,
            location=OpenApiParameter.PATH,
            description='진단 ID'
        )
    ]
)
@api_view(['GET'])
def get_condition_fhir(request, diagnosis_id):
    """
    FHIR Condition 리소스 조회

    진단 정보를 FHIR R4 Condition 리소스 형식으로 반환합니다.
    """
    try:
        encounter_diagnosis = get_object_or_404(EncounterDiagnosis, id=diagnosis_id)
        fhir_resource = ConditionConverter.to_fhir(encounter_diagnosis)
        return Response(fhir_resource, status=status.HTTP_200_OK)
    except Exception as e:
        return Response(
            {"error": str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@extend_schema(
    request=None,
    responses={200: dict},
    summary="FHIR ImagingStudy 리소스 조회",
    description="영상 검사 정보를 FHIR R4 ImagingStudy 리소스 형식으로 조회합니다.",
    tags=["FHIR"],
    parameters=[
        OpenApiParameter(
            name='study_id',
            type=str,
            location=OpenApiParameter.PATH,
            description='Study ID (UUID)'
        )
    ]
)
@api_view(['GET'])
def get_imaging_study_fhir(request, study_id):
    """
    FHIR ImagingStudy 리소스 조회

    영상 검사 정보를 FHIR R4 ImagingStudy 리소스 형식으로 반환합니다.
    """
    try:
        radiology_study = get_object_or_404(RadiologyStudy, study_id=study_id)
        fhir_resource = ImagingStudyConverter.to_fhir(radiology_study)
        return Response(fhir_resource, status=status.HTTP_200_OK)
    except Exception as e:
        return Response(
            {"error": str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@extend_schema(
    request=None,
    responses={200: dict},
    summary="FHIR Procedure 리소스 조회",
    description="시술 절차 정보를 FHIR R4 Procedure 리소스 형식으로 조회합니다.",
    tags=["FHIR"],
    parameters=[
        OpenApiParameter(
            name='order_id',
            type=str,
            location=OpenApiParameter.PATH,
            description='처방 ID (예: O-2025-000001)'
        )
    ]
)
@api_view(['GET'])
def get_procedure_fhir(request, order_id):
    """
    FHIR Procedure 리소스 조회

    시술 절차 정보를 FHIR R4 Procedure 리소스 형식으로 반환합니다.
    """
    try:
        order = get_object_or_404(Order, order_id=order_id, order_type='procedure')
        fhir_resource = ProcedureConverter.to_fhir(order)
        return Response(fhir_resource, status=status.HTTP_200_OK)
    except Exception as e:
        return Response(
            {"error": str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@extend_schema(
    request=FHIRSyncRequestSerializer,
    responses={201: FHIRSyncQueueSerializer},
    summary="FHIR 동기화 작업 생성",
    description="CDSS 리소스를 FHIR 서버로 동기화하는 작업을 큐에 추가합니다.",
    tags=["FHIR"],
    examples=[
        OpenApiExample(
            'Patient 동기화 요청',
            value={
                'resource_type': 'Patient',
                'cdss_id': 'P-2025-000001',
                'operation': 'create',
                'priority': 5
            }
        )
    ]
)
@api_view(['POST'])
def create_fhir_sync_task(request):
    """
    FHIR 동기화 작업 생성

    CDSS 리소스를 FHIR 서버로 동기화하는 작업을 큐에 추가합니다.

    **동기화 프로세스:**
    1. 요청된 CDSS 리소스 조회
    2. FHIR Resource로 변환
    3. FHIRSyncQueue에 작업 추가
    4. 백그라운드 워커가 FHIR 서버로 전송
    """
    serializer = FHIRSyncRequestSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)

    resource_type = serializer.validated_data['resource_type']
    cdss_id = serializer.validated_data['cdss_id']
    operation = serializer.validated_data['operation']
    priority = serializer.validated_data['priority']

    try:
        # 1. CDSS 리소스 조회 및 FHIR 변환
        fhir_payload = None
        if resource_type == 'Patient':
            patient = get_object_or_404(PatientCache, patient_id=cdss_id)
            fhir_payload = PatientConverter.to_fhir(patient)
        elif resource_type == 'Encounter':
            encounter = get_object_or_404(Encounter, encounter_id=cdss_id)
            fhir_payload = EncounterConverter.to_fhir(encounter)
        elif resource_type == 'Observation':
            lab_result = get_object_or_404(LabResult, result_id=cdss_id)
            fhir_payload = ObservationConverter.to_fhir(lab_result)
        elif resource_type == 'DiagnosticReport':
            ai_job = get_object_or_404(AIJob, job_id=int(cdss_id))
            fhir_payload = DiagnosticReportConverter.to_fhir(ai_job)
        elif resource_type == 'MedicationRequest':
            order = get_object_or_404(Order, order_id=cdss_id, order_type='medication')
            fhir_payload = MedicationRequestConverter.to_fhir(order)
        elif resource_type == 'ServiceRequest':
            try:
                radiology_order = RadiologyOrder.objects.get(order_id=cdss_id)
                fhir_payload = ServiceRequestConverter.to_fhir(radiology_order)
            except RadiologyOrder.DoesNotExist:
                order = get_object_or_404(Order, order_id=cdss_id)
                fhir_payload = ServiceRequestConverter.to_fhir(order)
        elif resource_type == 'Condition':
            diagnosis = get_object_or_404(EncounterDiagnosis, id=int(cdss_id))
            fhir_payload = ConditionConverter.to_fhir(diagnosis)
        elif resource_type == 'ImagingStudy':
            study = get_object_or_404(RadiologyStudy, study_id=cdss_id)
            fhir_payload = ImagingStudyConverter.to_fhir(study)
        elif resource_type == 'Procedure':
            order = get_object_or_404(Order, order_id=cdss_id, order_type='procedure')
            fhir_payload = ProcedureConverter.to_fhir(order)

        # 2. FHIRResourceMap 생성 또는 조회
        resource_map, created = FHIRResourceMap.objects.get_or_create(
            resource_type=resource_type,
            cdss_id=cdss_id,
            defaults={'fhir_id': f'{resource_type}/{cdss_id}'}
        )

        # 3. FHIRSyncQueue에 작업 추가
        sync_task = FHIRSyncQueue.objects.create(
            resource_map=resource_map,
            operation=operation,
            priority=priority,
            payload=fhir_payload
        )

        serializer = FHIRSyncQueueSerializer(sync_task)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    except Exception as e:
        return Response(
            {"error": str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

@extend_schema(
    summary="FHIR 서버 프록시",
    description="HAPI FHIR 서버로 요청을 전달합니다. (Metadata, Search 등)",
    tags=["FHIR"]
)
@api_view(['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS'])
@permission_classes([AllowAny])
def fhir_proxy(request, path):
    """HAPI FHIR 서버 프록시"""
    import requests
    from django.http import HttpResponse
    from django.conf import settings

    # FHIR_API_URL이 설정되지 않았을 경우 대비
    base_url = getattr(settings, 'FHIR_API_URL', 'http://hapi-fhir:8080/fhir')
    target_url = f"{base_url}/{path}"
    
    # Query Params 전달
    if request.query_params:
        target_url += f"?{request.GET.urlencode()}"

    try:
        # 헤더 전달 (Host 제외)
        headers = {k: v for k, v in request.headers.items() if k.lower() != 'host' and k.lower() != 'content-length'}
        
        # Content-Type 강제 지정 (FHIR R4)
        if 'application/fhir+json' not in headers.get('Accept', ''):
             headers['Accept'] = 'application/fhir+json'

        response = requests.request(
            method=request.method,
            url=target_url,
            headers=headers,
            data=request.body,
            timeout=10
        )
        
        return HttpResponse(
            content=response.content,
            status=response.status_code,
            content_type=response.headers.get('Content-Type')
        )
    except Exception as e:
        return Response({"error": f"FHIR Proxy failed: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

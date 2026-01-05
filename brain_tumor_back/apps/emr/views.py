from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
import os
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiExample
from drf_spectacular.types import OpenApiTypes
from .openemr_client import OpenEMRClient
from .serializers import PatientCreateSerializer, OrderCreateSerializer, PatientCacheSerializer, OrderSerializer
from .business_services import PatientService, OrderService

# OpenEMR 클라이언트 인스턴스
openemr_url = os.getenv('OPENEMR_BASE_URL', 'http://localhost:80')
client = OpenEMRClient(base_url=openemr_url)


@extend_schema(
    summary="OpenEMR 서버 상태 확인",
    description="OpenEMR 서버의 연결 상태와 API 가용성을 확인합니다.",
    tags=["emr"],
    responses={
        200: OpenApiTypes.OBJECT,
        500: OpenApiTypes.OBJECT,
    }
)
@require_http_methods(["GET"])
def health_check(request):
    """OpenEMR 서버 상태 확인"""
    result = client.health_check()
    return JsonResponse(result)


@extend_schema(
    summary="OpenEMR 인증",
    description="OpenEMR 시스템에 대한 인증 토큰을 발급받습니다.",
    tags=["emr"],
    request=OpenApiTypes.OBJECT,
    responses={
        200: OpenApiTypes.OBJECT,
        401: OpenApiTypes.OBJECT,
    }
)
@csrf_exempt
@require_http_methods(["POST"])
def authenticate(request):
    """OpenEMR 인증 API"""
    if request.method == 'POST':
        data = json.loads(request.body)
        username = data.get('username')
        password = data.get('password')

        result = client.authenticate(username, password)
        return JsonResponse(result)

    return JsonResponse({"error": "Method not allowed"}, status=405)


def test_dashboard(request):
    """테스트 시나리오 대시보드 뷰"""
    from django.shortcuts import render
    return render(request, 'emr/test_dashboard.html')

def test_ui_legacy(request):
    """[Legacy] OpenEMR 연동 테스트 UI 뷰"""
    from django.shortcuts import render
    return render(request, 'emr/emr_test_ui.html')

def comprehensive_test(request):
    """
    종합 테스트 대시보드 뷰

    모든 EMR CRUD, OpenEMR 연동, Write-Through 패턴을 통합한 테스트 페이지
    """
    from django.shortcuts import render
    return render(request, 'emr/comprehensive_crud_test.html')


@extend_schema(
    summary="환자 목록 조회",
    description="OpenEMR에서 환자 목록을 조회합니다. limit 파라미터로 조회 개수를 제한할 수 있습니다.",
    tags=["emr"],
    parameters=[
        OpenApiParameter(
            name="limit",
            type=OpenApiTypes.INT,
            location=OpenApiParameter.QUERY,
            description="조회할 환자 수 (기본값: 10)",
            required=False,
        ),
    ],
    responses={
        200: OpenApiTypes.OBJECT,
    }
)
@require_http_methods(["GET"])
def list_patients(request):
    """환자 목록 조회"""
    limit = int(request.GET.get('limit', 10))
    patients = client.get_patients(limit=limit)
    return JsonResponse({
        "count": len(patients),
        "results": patients
    })


@extend_schema(
    summary="환자 검색",
    description="이름(given name) 또는 성(family name)으로 환자를 검색합니다.",
    tags=["emr"],
    parameters=[
        OpenApiParameter(
            name="given",
            type=OpenApiTypes.STR,
            location=OpenApiParameter.QUERY,
            description="환자의 이름",
            required=False,
        ),
        OpenApiParameter(
            name="family",
            type=OpenApiTypes.STR,
            location=OpenApiParameter.QUERY,
            description="환자의 성",
            required=False,
        ),
    ],
    responses={
        200: OpenApiTypes.OBJECT,
    }
)
@require_http_methods(["GET"])
def search_patients(request):
    """환자 검색"""
    given = request.GET.get('given')
    family = request.GET.get('family')

    patients = client.search_patients(given=given, family=family)
    return JsonResponse({
        "count": len(patients),
        "results": patients
    })


@extend_schema(
    summary="특정 환자 조회",
    description="환자 ID로 특정 환자의 상세 정보를 조회합니다.",
    tags=["emr"],
    parameters=[
        OpenApiParameter(
            name="patient_id",
            type=OpenApiTypes.STR,
            location=OpenApiParameter.PATH,
            description="환자 ID (UUID)",
            required=True,
        ),
    ],
    responses={
        200: OpenApiTypes.OBJECT,
        404: OpenApiTypes.OBJECT,
    }
)
@require_http_methods(["GET"])
def get_patient(request, patient_id):
    """특정 환자 조회"""
    patient = client.get_patient(patient_id)

    if patient:
        return JsonResponse(patient)
    else:
        return JsonResponse({
            "error": "Patient not found"
        }, status=404)

@extend_schema(
    summary="EMR 데이터 검증",
    description="OpenEMR DB에 직접 연결하여 환자 데이터 저장 상태를 검증합니다.",
    tags=["emr"],
    parameters=[
        OpenApiParameter(
            name="patient_id",
            type=OpenApiTypes.STR,
            location=OpenApiParameter.PATH,
            description="검증할 환자 ID",
            required=True,
        ),
    ],
    responses={
        200: OpenApiTypes.OBJECT,
        404: OpenApiTypes.OBJECT,
    }
)
@require_http_methods(["GET"])
def verify_emr_data(request, patient_id):
    """OpenEMR DB 직접 조회를 통한 데이터 저장 검증 (Proof)"""
    from .repositories import OpenEMRPatientRepository
    
    emr_data = OpenEMRPatientRepository.get_patient_by_pubpid(patient_id)
    
    if emr_data:
        return JsonResponse({
            "status": "Verified",
            "source": "OpenEMR (emr_db.patient_data)",
            "verified_at": datetime.now().isoformat(),
            "emr_entry": emr_data
        })
    else:
        return JsonResponse({
            "status": "Failed",
            "message": "OpenEMR 데이터베이스에 해당 데이터가 존재하지 않습니다."
        }, status=404)


class PatientCreateView(APIView):
    """
    환자 생성 Controller
    - DTO 검증 (Serializer)
    - Service 호출 (Business Logic)
    """
    def post(self, request):
        serializer = PatientCreateSerializer(data=request.data)
        if serializer.is_valid():
            # PatientService.create_patient는 (patient_obj, status_dict) 튜플을 반환함
            patient, status_info = PatientService.create_patient(serializer.validated_data)
            # 응답용 Serializer로 변환
            response_serializer = PatientCacheSerializer(patient)
            
            # 상세 상태 정보를 헤더나 메타데이터에 포함할 수도 있으나, 일단 성공 응답 반환
            return Response({
                "patient": response_serializer.data,
                "persistence_status": status_info
            }, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class OrderCreateView(APIView):
    """
    처방 생성 Controller
    - DTO 검증 (Serializer)
    - Service 호출 (Business Logic)
    """
    def post(self, request):
        serializer = OrderCreateSerializer(data=request.data)
        if serializer.is_valid():
            order_data = serializer.validated_data
            # order_items 분리
            items_data = order_data.pop('order_items', [])
            
            order = OrderService.create_order(order_data, items_data)
            
            # 응답용 Serializer로 변환
            response_serializer = OrderSerializer(order)
            return Response(response_serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

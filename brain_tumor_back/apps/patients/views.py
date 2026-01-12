from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.pagination import PageNumberPagination
from django.core.exceptions import ObjectDoesNotExist
from django.utils import timezone

from .models import Patient
from .serializers import (
    PatientListSerializer,
    PatientDetailSerializer,
    PatientCreateSerializer,
    PatientUpdateSerializer,
    PatientSearchSerializer,
)
from .services import PatientService


class PatientPagination(PageNumberPagination):
    """환자 목록 페이지네이션"""
    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 100


@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def patient_list_create(request):
    """
    환자 목록 조회 및 등록

    GET: 환자 목록 조회
    POST: 환자 등록
    """
    if request.method == 'GET':
        # 검색 필터 처리
        search_serializer = PatientSearchSerializer(data=request.query_params)
        if not search_serializer.is_valid():
            return Response(
                search_serializer.errors,
                status=status.HTTP_400_BAD_REQUEST
            )

        filters = search_serializer.validated_data
        patients = PatientService.get_all_patients(filters)

        # 페이지네이션
        paginator = PatientPagination()
        page = paginator.paginate_queryset(patients, request)

        if page is not None:
            serializer = PatientListSerializer(page, many=True)
            return paginator.get_paginated_response(serializer.data)

        serializer = PatientListSerializer(patients, many=True)
        return Response(serializer.data)

    elif request.method == 'POST':
        serializer = PatientCreateSerializer(
            data=request.data,
            context={'request': request}
        )

        if serializer.is_valid():
            try:
                patient = PatientService.create_patient(
                    serializer.validated_data,
                    request.user
                )
                return Response(
                    PatientDetailSerializer(patient).data,
                    status=status.HTTP_201_CREATED
                )
            except Exception as e:
                return Response(
                    {'error': str(e)},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET', 'PUT', 'DELETE'])
@permission_classes([IsAuthenticated])
def patient_detail(request, patient_id):
    """
    환자 상세 조회, 수정, 삭제

    GET: 환자 상세 조회
    PUT: 환자 정보 수정
    DELETE: 환자 삭제 (Soft Delete)
    """
    try:
        if request.method == 'GET':
            patient = PatientService.get_patient_by_id(patient_id)
            # TODO: Add audit log
            serializer = PatientDetailSerializer(patient)
            return Response(serializer.data)

        elif request.method == 'PUT':
            serializer = PatientUpdateSerializer(data=request.data)

            if serializer.is_valid():
                patient = PatientService.update_patient(
                    patient_id,
                    serializer.validated_data,
                    request.user
                )
                return Response(PatientDetailSerializer(patient).data)

            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        elif request.method == 'DELETE':
            patient = PatientService.delete_patient(patient_id, request.user)
            return Response(
                {'message': '환자가 삭제되었습니다.'},
                status=status.HTTP_204_NO_CONTENT
            )

    except ObjectDoesNotExist:
        return Response(
            {'error': '환자를 찾을 수 없습니다.'},
            status=status.HTTP_404_NOT_FOUND
        )
    except Exception as e:
        return Response(
            {'error': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def patient_search(request):
    """
    환자 통합 검색 (자동완성용)

    Query Parameters:
        q: 검색어
    """
    query = request.query_params.get('q', '').strip()

    if not query:
        return Response([])

    if len(query) < 2:
        return Response(
            {'error': '검색어는 2자 이상 입력해주세요.'},
            status=status.HTTP_400_BAD_REQUEST
        )

    patients = PatientService.search_patients(query)
    serializer = PatientListSerializer(patients, many=True)

    return Response(serializer.data)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def patient_statistics(request):
    """
    환자 통계 조회

    Returns:
        환자 총계, 활성/비활성 수, 성별 통계 등
    """
    stats = PatientService.get_patient_statistics()
    return Response(stats)


def _generate_external_patient_number():
    """외부 환자용 환자번호 생성 (EXTR_0001 형식)"""
    last_external = Patient.objects.filter(
        patient_number__startswith='EXTR_'
    ).order_by('-patient_number').first()

    if last_external and last_external.patient_number:
        try:
            last_num = int(last_external.patient_number.split('_')[1])
            return f"EXTR_{last_num + 1:04d}"
        except (ValueError, IndexError):
            pass
    return "EXTR_0001"


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_external_patient(request):
    """
    외부 기관 환자 등록

    외부 검사 결과를 업로드할 때 환자가 시스템에 등록되지 않은 경우
    간소화된 정보로 환자를 등록합니다.

    Required fields:
        - name: 환자명
        - birth_date: 생년월일 (YYYY-MM-DD)
        - gender: 성별 (M/F/O)

    Optional fields:
        - phone: 전화번호
        - institution_name: 외부 기관명
        - external_patient_id: 외부 기관의 환자 ID
    """
    # 필수 필드 검증
    name = request.data.get('name')
    birth_date = request.data.get('birth_date')
    gender = request.data.get('gender')

    if not all([name, birth_date, gender]):
        return Response(
            {'error': '필수 정보가 누락되었습니다. (이름, 생년월일, 성별)'},
            status=status.HTTP_400_BAD_REQUEST
        )

    # 성별 검증
    if gender not in ['M', 'F', 'O']:
        return Response(
            {'error': '성별은 M, F, O 중 하나여야 합니다.'},
            status=status.HTTP_400_BAD_REQUEST
        )

    # 생년월일 형식 검증
    from datetime import datetime
    try:
        birth_date_parsed = datetime.strptime(birth_date, '%Y-%m-%d').date()
    except ValueError:
        return Response(
            {'error': '생년월일 형식이 올바르지 않습니다. (YYYY-MM-DD)'},
            status=status.HTTP_400_BAD_REQUEST
        )

    # 외부 환자번호 생성
    patient_number = _generate_external_patient_number()

    # 외부 기관 정보 (메타데이터로 저장)
    external_info = {}
    if request.data.get('institution_name'):
        external_info['institution_name'] = request.data.get('institution_name')
    if request.data.get('external_patient_id'):
        external_info['external_patient_id'] = request.data.get('external_patient_id')

    # SSN 생성 (외부 환자는 가상의 SSN 사용)
    # 형식: EXTR_{환자번호}_{타임스탬프}
    import time
    virtual_ssn = f"EXTR_{patient_number}_{int(time.time())}"

    try:
        patient = Patient.objects.create(
            patient_number=patient_number,
            name=name,
            birth_date=birth_date_parsed,
            gender=gender,
            phone=request.data.get('phone', '000-0000-0000'),  # 기본값
            ssn=virtual_ssn,
            address=request.data.get('address', ''),
            status='active',
            registered_by=request.user,
            # 외부 환자 관련 메타 정보는 chronic_diseases JSON 필드 활용
            chronic_diseases=external_info if external_info else [],
        )

        return Response({
            'message': '외부 환자가 등록되었습니다.',
            'patient': PatientDetailSerializer(patient).data
        }, status=status.HTTP_201_CREATED)

    except Exception as e:
        return Response(
            {'error': f'환자 등록 중 오류가 발생했습니다: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def patient_summary(request, patient_id):
    """
    환자 요약서 데이터 조회 (PDF 생성용)

    Returns:
        - patient: 기본정보 (이름, 나이, 성별, 연락처, 주소)
        - encounters: 최근 진료이력 (최근 10건)
        - ocs_history: OCS (RIS/LIS) 검사이력 (최근 10건)
        - ai_inferences: AI 추론이력 (최근 5건)
        - treatment_plans: 치료계획 (최근 5건)
        - prescriptions: 처방이력 (최근 10건)
        - generated_at: 생성 시각
    """
    try:
        patient = PatientService.get_patient_by_id(patient_id)
    except ObjectDoesNotExist:
        return Response(
            {'error': '환자를 찾을 수 없습니다.'},
            status=status.HTTP_404_NOT_FOUND
        )

    # 기본 정보
    patient_data = PatientDetailSerializer(patient).data

    # 진료 이력 (최근 10건)
    from apps.encounters.models import Encounter
    from apps.encounters.serializers import EncounterListSerializer
    encounters = Encounter.objects.filter(
        patient=patient, is_deleted=False
    ).order_by('-admission_date')[:10]
    encounter_data = EncounterListSerializer(encounters, many=True).data

    # OCS 이력 (최근 10건)
    from apps.ocs.models import OCS
    from apps.ocs.serializers import OCSListSerializer
    ocs_list = OCS.objects.filter(
        patient=patient, is_deleted=False
    ).order_by('-created_at')[:10]
    ocs_data = OCSListSerializer(ocs_list, many=True).data

    # AI 추론 이력 (최근 5건)
    from apps.ai_inference.models import AIInferenceRequest
    from apps.ai_inference.serializers import AIInferenceRequestListSerializer
    ai_requests = AIInferenceRequest.objects.filter(
        patient=patient
    ).order_by('-created_at')[:5]
    ai_data = AIInferenceRequestListSerializer(ai_requests, many=True).data

    # 치료 계획 (최근 5건)
    try:
        from apps.treatment.models import TreatmentPlan
        from apps.treatment.serializers import TreatmentPlanListSerializer
        treatment_plans = TreatmentPlan.objects.filter(
            patient=patient, is_deleted=False
        ).order_by('-created_at')[:5]
        treatment_data = TreatmentPlanListSerializer(treatment_plans, many=True).data
    except Exception:
        treatment_data = []

    # 처방 이력 (최근 10건)
    try:
        from apps.prescriptions.models import Prescription
        from apps.prescriptions.serializers import PrescriptionListSerializer
        prescriptions = Prescription.objects.filter(
            patient=patient
        ).order_by('-prescribed_at')[:10]
        prescription_data = PrescriptionListSerializer(prescriptions, many=True).data
    except Exception:
        prescription_data = []

    return Response({
        'patient': patient_data,
        'encounters': encounter_data,
        'ocs_history': ocs_data,
        'ai_inferences': ai_data,
        'treatment_plans': treatment_data,
        'prescriptions': prescription_data,
        'generated_at': timezone.now().isoformat()
    })

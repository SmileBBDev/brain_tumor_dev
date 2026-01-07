from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.pagination import PageNumberPagination
from django.core.exceptions import ObjectDoesNotExist

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

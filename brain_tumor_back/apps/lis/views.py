from rest_framework import viewsets, status, filters
from rest_framework.response import Response
from rest_framework.decorators import action
from drf_spectacular.utils import extend_schema_view, extend_schema, OpenApiParameter
from drf_spectacular.types import OpenApiTypes
from .models import LabTestMaster, LabResult
from .serializers import (
    LabTestMasterSerializer, LabResultSerializer, LabResultCreateSerializer
)
from .services import LabResultService

@extend_schema_view(
    list=extend_schema(
        summary="검사 항목 목록 조회",
        description="활성화된 검사 마스터 데이터 목록을 조회합니다. search 파라미터로 검사코드, 검사명, 검체종류 검색이 가능합니다.",
        tags=["lis"]
    ),
    retrieve=extend_schema(
        summary="검사 항목 상세 조회",
        description="특정 검사 항목의 상세 정보를 조회합니다.",
        tags=["lis"]
    ),
)
class LabTestMasterViewSet(viewsets.ReadOnlyModelViewSet):
    """
    검사 마스터 데이터 조회 API
    """
    queryset = LabTestMaster.objects.filter(is_active=True)
    serializer_class = LabTestMasterSerializer
    filter_backends = [filters.SearchFilter]
    search_fields = ['test_code', 'test_name', 'sample_type']

@extend_schema_view(
    list=extend_schema(
        summary="검사 결과 목록 조회",
        description="모든 검사 결과 목록을 조회합니다.",
        tags=["lis"]
    ),
    retrieve=extend_schema(
        summary="검사 결과 상세 조회",
        description="특정 검사 결과의 상세 정보를 조회합니다.",
        tags=["lis"]
    ),
    create=extend_schema(
        summary="검사 결과 등록",
        description="새로운 검사 결과를 등록합니다. Service 레이어를 통해 비즈니스 로직을 처리합니다.",
        tags=["lis"]
    ),
    update=extend_schema(
        summary="검사 결과 수정",
        description="검사 결과 정보를 수정합니다.",
        tags=["lis"]
    ),
    partial_update=extend_schema(
        summary="검사 결과 부분 수정",
        description="검사 결과 정보를 부분적으로 수정합니다.",
        tags=["lis"]
    ),
    destroy=extend_schema(
        summary="검사 결과 삭제",
        description="검사 결과를 삭제합니다.",
        tags=["lis"]
    ),
)
class LabResultViewSet(viewsets.ModelViewSet):
    """
    검사 결과 CRUD API
    """
    queryset = LabResult.objects.select_related('order', 'patient', 'test_master').all()
    serializer_class = LabResultSerializer

    def get_serializer_class(self):
        if self.action == 'create':
            return LabResultCreateSerializer
        return LabResultSerializer

    def create(self, request, *args, **kwargs):
        """검사 결과 등록 (Service 레이어 사용)"""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            result = LabResultService.create_lab_result(serializer.validated_data)
            response_serializer = LabResultSerializer(result)
            return Response(response_serializer.data, status=status.HTTP_201_CREATED)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

    @extend_schema(
        summary="환자별 검사 이력 조회",
        description="특정 환자의 모든 검사 이력을 조회합니다.",
        tags=["lis"],
        parameters=[
            OpenApiParameter(
                name="patient_id",
                type=OpenApiTypes.UUID,
                location=OpenApiParameter.QUERY,
                description="환자 ID (UUID)",
                required=True,
            ),
        ],
    )
    @action(detail=False, methods=['get'])
    def by_patient(self, request):
        """특정 환자의 검사 이력 조회"""
        patient_id = request.query_params.get('patient_id')
        if not patient_id:
            return Response({"error": "patient_id is required"}, status=status.HTTP_400_BAD_REQUEST)

        results = LabResultService.get_patient_lab_history(patient_id)
        serializer = self.get_serializer(results, many=True)
        return Response(serializer.data)

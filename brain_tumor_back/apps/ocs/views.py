from rest_framework import viewsets, filters
from drf_spectacular.utils import extend_schema_view, extend_schema
from .models import MedicationMaster, DiagnosisMaster
from .serializers import MedicationMasterSerializer, DiagnosisMasterSerializer

@extend_schema_view(
    list=extend_schema(
        summary="약물 목록 조회",
        description="활성화된 약물 마스터 데이터 목록을 조회합니다. search 파라미터로 약물코드, 약물명, 성분명 검색이 가능합니다.",
        tags=["ocs"]
    ),
    retrieve=extend_schema(
        summary="약물 상세 조회",
        description="특정 약물의 상세 정보를 조회합니다.",
        tags=["ocs"]
    ),
)
class MedicationMasterViewSet(viewsets.ReadOnlyModelViewSet):
    """
    약물 마스터 데이터 조회 API
    """
    queryset = MedicationMaster.objects.filter(is_active=True)
    serializer_class = MedicationMasterSerializer
    filter_backends = [filters.SearchFilter]
    search_fields = ['drug_code', 'drug_name', 'generic_name']

@extend_schema_view(
    list=extend_schema(
        summary="진단 목록 조회",
        description="활성화된 진단 마스터 데이터 목록을 조회합니다. search 파라미터로 진단코드, 한글명, 영문명 검색이 가능합니다.",
        tags=["ocs"]
    ),
    retrieve=extend_schema(
        summary="진단 상세 조회",
        description="특정 진단의 상세 정보를 조회합니다.",
        tags=["ocs"]
    ),
)
class DiagnosisMasterViewSet(viewsets.ReadOnlyModelViewSet):
    """
    진단 마스터 데이터 조회 API
    """
    queryset = DiagnosisMaster.objects.filter(is_active=True)
    serializer_class = DiagnosisMasterSerializer
    filter_backends = [filters.SearchFilter]
    search_fields = ['diag_code', 'name_ko', 'name_en']

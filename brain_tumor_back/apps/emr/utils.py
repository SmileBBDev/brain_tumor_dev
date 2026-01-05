from rest_framework import status
from rest_framework.decorators import action
from rest_framework.response import Response
from drf_spectacular.utils import extend_schema, OpenApiParameter

class ByPatientMixin:
    """특정 환자 ID로 필터링하는 공통 액션 상속용 믹스인"""
    
    @extend_schema(
        parameters=[
            OpenApiParameter("patient_id", type=str, description="환자 ID", required=True)
        ],
        summary="환자별 목록 조회",
        tags=['emr']
    )
    @action(detail=False, methods=['get'])
    def by_patient(self, request):
        patient_id = request.query_params.get('patient_id')
        if not patient_id:
            return Response(
                {"error": "patient_id is required"},
                status=status.HTTP_400_BAD_REQUEST
            )

        queryset = self.get_queryset().filter(patient_id=patient_id)
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

class ServiceCreateMixin:
    """Service를 호출하여 리소스를 생성하고 표준 응답을 반환하는 공통 믹스인"""
    
    def perform_service_create(self, service_func, serializer_class, data, **extra_kwargs):
        serializer = serializer_class(data=data)
        serializer.is_valid(raise_exception=True)
        
        # Service 호출
        instance, persistence_status = service_func(serializer.validated_data, **extra_kwargs)
        
        # 응답용 시리얼라이저 (동일한 클래스 또는 별도 클래스 사용 가능)
        response_serializer_class = self.get_serializer_class()
        response_serializer = response_serializer_class(instance)
        
        return Response({
            "data": response_serializer.data,
            "persistence_status": persistence_status
        }, status=status.HTTP_201_CREATED)

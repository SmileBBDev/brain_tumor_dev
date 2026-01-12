from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.utils import timezone
from django.db.models import Max

from .models import Prescription, PrescriptionItem
from .serializers import (
    PrescriptionListSerializer,
    PrescriptionDetailSerializer,
    PrescriptionCreateSerializer,
    PrescriptionUpdateSerializer,
    PrescriptionIssueSerializer,
    PrescriptionCancelSerializer,
    PrescriptionItemSerializer
)


class PrescriptionViewSet(viewsets.ModelViewSet):
    """
    처방전 ViewSet
    
    - GET /api/prescriptions/ : 처방전 목록
    - POST /api/prescriptions/ : 처방전 생성
    - GET /api/prescriptions/{id}/ : 처방전 상세
    - PATCH /api/prescriptions/{id}/ : 처방전 수정
    - POST /api/prescriptions/{id}/issue/ : 처방전 발행
    - POST /api/prescriptions/{id}/cancel/ : 처방전 취소
    - POST /api/prescriptions/{id}/items/ : 항목 추가
    - DELETE /api/prescriptions/{id}/items/{item_id}/ : 항목 삭제
    """
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        queryset = Prescription.objects.select_related(
            'patient', 'doctor', 'encounter'
        ).prefetch_related('items')

        # 필터링
        patient_id = self.request.query_params.get('patient_id')
        if patient_id:
            queryset = queryset.filter(patient_id=patient_id)

        doctor_id = self.request.query_params.get('doctor_id')
        if doctor_id:
            queryset = queryset.filter(doctor_id=doctor_id)

        encounter_id = self.request.query_params.get('encounter_id')
        if encounter_id:
            queryset = queryset.filter(encounter_id=encounter_id)

        status_filter = self.request.query_params.get('status')
        if status_filter:
            queryset = queryset.filter(status=status_filter)

        # 내 처방만 보기
        my_only = self.request.query_params.get('my_only')
        if my_only == 'true':
            queryset = queryset.filter(doctor=self.request.user)

        # 날짜 범위 필터
        start_date = self.request.query_params.get('start_date')
        if start_date:
            queryset = queryset.filter(created_at__date__gte=start_date)

        end_date = self.request.query_params.get('end_date')
        if end_date:
            queryset = queryset.filter(created_at__date__lte=end_date)

        return queryset.order_by('-created_at')

    def get_serializer_class(self):
        if self.action == 'list':
            return PrescriptionListSerializer
        if self.action == 'create':
            return PrescriptionCreateSerializer
        if self.action in ['update', 'partial_update']:
            return PrescriptionUpdateSerializer
        if self.action == 'issue':
            return PrescriptionIssueSerializer
        if self.action == 'cancel':
            return PrescriptionCancelSerializer
        return PrescriptionDetailSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        prescription = serializer.save()
        
        # 상세 정보 반환
        detail_serializer = PrescriptionDetailSerializer(prescription)
        return Response(detail_serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['post'])
    def issue(self, request, pk=None):
        """처방전 발행"""
        prescription = self.get_object()

        if prescription.status != Prescription.Status.DRAFT:
            return Response(
                {'error': '작성 중인 처방전만 발행할 수 있습니다.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        if prescription.items.count() == 0:
            return Response(
                {'error': '처방 항목이 없습니다.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        prescription.status = Prescription.Status.ISSUED
        prescription.issued_at = timezone.now()
        prescription.save()

        serializer = PrescriptionDetailSerializer(prescription)
        return Response({
            'message': '처방전이 발행되었습니다.',
            'prescription': serializer.data
        })

    @action(detail=True, methods=['post'])
    def cancel(self, request, pk=None):
        """처방전 취소"""
        prescription = self.get_object()

        if prescription.status in [Prescription.Status.DISPENSED, Prescription.Status.CANCELLED]:
            return Response(
                {'error': '이미 조제 완료되었거나 취소된 처방전입니다.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        serializer = PrescriptionCancelSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        prescription.status = Prescription.Status.CANCELLED
        prescription.cancelled_at = timezone.now()
        prescription.cancel_reason = serializer.validated_data['cancel_reason']
        prescription.save()

        detail_serializer = PrescriptionDetailSerializer(prescription)
        return Response({
            'message': '처방전이 취소되었습니다.',
            'prescription': detail_serializer.data
        })

    @action(detail=True, methods=['post'])
    def dispense(self, request, pk=None):
        """처방전 조제 완료 처리"""
        prescription = self.get_object()

        if prescription.status != Prescription.Status.ISSUED:
            return Response(
                {'error': '발행된 처방전만 조제 완료 처리할 수 있습니다.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        prescription.status = Prescription.Status.DISPENSED
        prescription.dispensed_at = timezone.now()
        prescription.save()

        serializer = PrescriptionDetailSerializer(prescription)
        return Response({
            'message': '조제가 완료되었습니다.',
            'prescription': serializer.data
        })

    @action(detail=True, methods=['post'], url_path='items')
    def add_item(self, request, pk=None):
        """처방 항목 추가"""
        prescription = self.get_object()

        if not prescription.is_editable:
            return Response(
                {'error': '발행된 처방전은 수정할 수 없습니다.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        serializer = PrescriptionItemSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        # 순서 자동 설정
        max_order = prescription.items.aggregate(Max('order'))['order__max'] or 0
        
        item = PrescriptionItem.objects.create(
            prescription=prescription,
            order=max_order + 1,
            **serializer.validated_data
        )

        return Response(
            PrescriptionItemSerializer(item).data,
            status=status.HTTP_201_CREATED
        )

    @action(detail=True, methods=['delete'], url_path='items/(?P<item_id>[^/.]+)')
    def remove_item(self, request, pk=None, item_id=None):
        """처방 항목 삭제"""
        prescription = self.get_object()

        if not prescription.is_editable:
            return Response(
                {'error': '발행된 처방전은 수정할 수 없습니다.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            item = prescription.items.get(id=item_id)
            item.delete()
            return Response({'message': '항목이 삭제되었습니다.'})
        except PrescriptionItem.DoesNotExist:
            return Response(
                {'error': '존재하지 않는 항목입니다.'},
                status=status.HTTP_404_NOT_FOUND
            )

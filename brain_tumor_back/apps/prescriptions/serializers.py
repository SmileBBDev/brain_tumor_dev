from rest_framework import serializers
from django.utils import timezone
from .models import Prescription, PrescriptionItem
from apps.patients.models import Patient


class PrescriptionItemSerializer(serializers.ModelSerializer):
    """처방 항목 시리얼라이저"""
    frequency_display = serializers.CharField(source='get_frequency_display', read_only=True)
    route_display = serializers.CharField(source='get_route_display', read_only=True)

    class Meta:
        model = PrescriptionItem
        fields = [
            'id', 'medication_name', 'medication_code', 'dosage',
            'frequency', 'frequency_display', 'route', 'route_display',
            'duration_days', 'quantity', 'instructions', 'order',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']


class PrescriptionItemCreateSerializer(serializers.ModelSerializer):
    """처방 항목 생성용 시리얼라이저"""

    class Meta:
        model = PrescriptionItem
        fields = [
            'medication_name', 'medication_code', 'dosage',
            'frequency', 'route', 'duration_days', 'quantity',
            'instructions', 'order'
        ]


class PrescriptionListSerializer(serializers.ModelSerializer):
    """처방전 목록용 시리얼라이저"""
    patient_name = serializers.CharField(source='patient.name', read_only=True)
    patient_number = serializers.CharField(source='patient.patient_number', read_only=True)
    doctor_name = serializers.SerializerMethodField()
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    item_count = serializers.SerializerMethodField()

    class Meta:
        model = Prescription
        fields = [
            'id', 'prescription_id', 'patient', 'patient_name', 'patient_number',
            'doctor', 'doctor_name', 'encounter', 'status', 'status_display',
            'diagnosis', 'item_count', 'created_at', 'issued_at'
        ]

    def get_doctor_name(self, obj):
        """doctor가 None일 경우 처리"""
        if obj.doctor:
            return obj.doctor.name
        return None

    def get_item_count(self, obj):
        """item_count - prefetch된 items 사용"""
        return obj.items.count()


class PrescriptionDetailSerializer(serializers.ModelSerializer):
    """처방전 상세 시리얼라이저"""
    patient_name = serializers.CharField(source='patient.name', read_only=True)
    patient_number = serializers.CharField(source='patient.patient_number', read_only=True)
    patient_birth_date = serializers.DateField(source='patient.birth_date', read_only=True)
    patient_gender = serializers.CharField(source='patient.gender', read_only=True)
    doctor_name = serializers.SerializerMethodField()
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    items = PrescriptionItemSerializer(many=True, read_only=True)
    is_editable = serializers.BooleanField(read_only=True)

    def get_doctor_name(self, obj):
        """doctor가 None일 경우 처리"""
        if obj.doctor:
            return obj.doctor.name
        return None

    class Meta:
        model = Prescription
        fields = [
            'id', 'prescription_id', 
            'patient', 'patient_name', 'patient_number', 'patient_birth_date', 'patient_gender',
            'doctor', 'doctor_name', 'encounter',
            'status', 'status_display', 'diagnosis', 'notes',
            'items', 'is_editable',
            'created_at', 'issued_at', 'dispensed_at', 'cancelled_at', 'updated_at',
            'cancel_reason'
        ]
        read_only_fields = ['prescription_id', 'created_at', 'updated_at']


class PrescriptionCreateSerializer(serializers.ModelSerializer):
    """처방전 생성 시리얼라이저"""
    patient_id = serializers.IntegerField(write_only=True)
    encounter_id = serializers.IntegerField(write_only=True, required=False, allow_null=True)
    items = PrescriptionItemCreateSerializer(many=True, write_only=True, required=False)

    class Meta:
        model = Prescription
        fields = ['patient_id', 'encounter_id', 'diagnosis', 'notes', 'items']

    def validate_patient_id(self, value):
        try:
            Patient.objects.get(id=value)
        except Patient.DoesNotExist:
            raise serializers.ValidationError('존재하지 않는 환자입니다.')
        return value

    def create(self, validated_data):
        patient_id = validated_data.pop('patient_id')
        encounter_id = validated_data.pop('encounter_id', None)
        items_data = validated_data.pop('items', [])
        user = self.context['request'].user

        prescription = Prescription.objects.create(
            patient_id=patient_id,
            doctor=user,
            encounter_id=encounter_id,
            **validated_data
        )

        # 처방 항목 생성
        for idx, item_data in enumerate(items_data):
            item_data['order'] = idx
            PrescriptionItem.objects.create(prescription=prescription, **item_data)

        return prescription


class PrescriptionUpdateSerializer(serializers.ModelSerializer):
    """처방전 수정 시리얼라이저"""
    items = PrescriptionItemCreateSerializer(many=True, required=False)

    class Meta:
        model = Prescription
        fields = ['diagnosis', 'notes', 'items']

    def validate(self, attrs):
        if self.instance and not self.instance.is_editable:
            raise serializers.ValidationError('발행된 처방전은 수정할 수 없습니다.')
        return attrs

    def update(self, instance, validated_data):
        items_data = validated_data.pop('items', None)

        # 기본 필드 업데이트
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        # 항목 업데이트 (전체 교체 방식)
        if items_data is not None:
            instance.items.all().delete()
            for idx, item_data in enumerate(items_data):
                item_data['order'] = idx
                PrescriptionItem.objects.create(prescription=instance, **item_data)

        return instance


class PrescriptionIssueSerializer(serializers.Serializer):
    """처방전 발행 시리얼라이저"""
    pass  # 추가 데이터 없이 발행


class PrescriptionCancelSerializer(serializers.Serializer):
    """처방전 취소 시리얼라이저"""
    cancel_reason = serializers.CharField(max_length=200, required=True)

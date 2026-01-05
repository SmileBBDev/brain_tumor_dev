"""
EMR Serializers

Django REST Framework용 시리얼라이저
"""

from rest_framework import serializers
from drf_spectacular.utils import extend_schema_field
from drf_spectacular.types import OpenApiTypes
from .models import PatientCache, Encounter, EncounterDiagnosis, Order, OrderItem
from utils.validators import (
    validate_ssn_kr,
    validate_phone_kr,
    validate_email,
    validate_birth_date,
    UniqueFieldValidator,
)


class PatientValidationMixin:
    """환자 데이터 검증 공통 로직을 담은 믹스인 (리팩토링: 공통 validators 사용)"""

    def validate_ssn(self, value):
        """주민등록번호 검증 (형식 + 체크섬 + 중복 체크)"""
        # 형식 및 체크섬 검증
        value = validate_ssn_kr(value)
        # 중복 검증
        return UniqueFieldValidator.validate(self, 'ssn', value, '주민등록번호')

    def validate_phone(self, value):
        """전화번호 형식 검증"""
        return validate_phone_kr(value)

    def validate_email(self, value):
        """이메일 형식 검증"""
        return validate_email(value)

    def validate_birth_date(self, value):
        """생년월일 검증 (미래 날짜 불가)"""
        return validate_birth_date(value)


class PatientCacheSerializer(PatientValidationMixin, serializers.ModelSerializer):
    """환자 캐시 시리얼라이저"""
    @extend_schema_field(OpenApiTypes.STR)
    def get_full_name(self, obj):
        return obj.full_name

    @extend_schema_field(OpenApiTypes.BOOL)
    def get_is_synced(self, obj):
        return obj.is_synced

    full_name = serializers.SerializerMethodField()
    is_synced = serializers.SerializerMethodField()

    class Meta:
        model = PatientCache
        fields = [
            'patient_id', 'family_name', 'given_name', 'birth_date', 'gender',
            'phone', 'email', 'address', 'ssn', 'emergency_contact', 'allergies',
            'blood_type', 'openemr_patient_id', 'last_synced_at',
            'created_at', 'updated_at', 'full_name', 'is_synced'
        ]
        read_only_fields = ['patient_id', 'created_at', 'updated_at']


class PatientCreateSerializer(PatientValidationMixin, serializers.ModelSerializer):
    """환자 생성 시리얼라이저"""

    class Meta:
        model = PatientCache
        fields = [
            'family_name', 'given_name', 'birth_date', 'gender',
            'phone', 'email', 'address', 'ssn', 'emergency_contact', 'allergies', 'blood_type'
        ]



class EncounterDiagnosisSerializer(serializers.ModelSerializer):
    """진료 진단 시리얼라이저"""
    class Meta:
        model = EncounterDiagnosis
        fields = ['diag_code', 'diagnosis_name', 'comments', 'priority', 'created_at']


class EncounterSerializer(serializers.ModelSerializer):
    """진료 기록 시리얼라이저"""
    patient_name = serializers.SerializerMethodField()
    diagnoses = EncounterDiagnosisSerializer(many=True, read_only=True)

    class Meta:
        model = Encounter
        fields = [
            'encounter_id', 'patient', 'patient_name', 'doctor',
            'encounter_type', 'department', 'chief_complaint', 'diagnosis',
            'status', 'encounter_date', 'diagnoses', 'created_at', 'updated_at'
        ]
        read_only_fields = ['encounter_id', 'created_at', 'updated_at']

    @extend_schema_field(OpenApiTypes.STR)
    def get_patient_name(self, obj):
        return obj.patient.full_name


class EncounterCreateSerializer(serializers.ModelSerializer):
    """진료 기록 생성 시리얼라이저"""
    diagnoses = serializers.ListField(
        child=serializers.DictField(),
        write_only=True,
        required=False
    )

    class Meta:
        model = Encounter
        fields = [
            'patient', 'doctor', 'encounter_type', 'department',
            'chief_complaint', 'diagnosis', 'diagnoses', 'status', 'encounter_date'
        ]


class OrderItemSerializer(serializers.ModelSerializer):
    """처방 항목 시리얼라이저"""
    master_info = serializers.JSONField(read_only=True)

    class Meta:
        model = OrderItem
        fields = [
            'item_id', 'drug_code', 'drug_name', 'dosage',
            'frequency', 'duration', 'route', 'instructions', 'master_info'
        ]
        read_only_fields = ['item_id']


class OrderSerializer(serializers.ModelSerializer):
    """처방 시리얼라이저 (조회용)"""
    items = OrderItemSerializer(many=True, read_only=True)
    patient_name = serializers.SerializerMethodField()

    class Meta:
        model = Order
        fields = [
            'order_id', 'patient', 'patient_name', 'encounter', 'ordered_by',
            'order_type', 'urgency', 'status', 'notes',
            'ordered_at', 'executed_at', 'executed_by', 'items'
        ]
        read_only_fields = ['order_id', 'ordered_at']

    @extend_schema_field(OpenApiTypes.STR)
    def get_patient_name(self, obj):
        return obj.patient.full_name


class OrderCreateSerializer(serializers.ModelSerializer):
    """처방 생성 시리얼라이저"""
    order_items = serializers.ListField(
        child=serializers.DictField(),
        write_only=True,
        required=False
    )

    class Meta:
        model = Order
        fields = [
            'patient', 'encounter', 'ordered_by', 'order_type',
            'urgency', 'status', 'notes', 'order_items'
        ]


class OrderItemUpdateSerializer(serializers.ModelSerializer):
    """처방 항목 수정 시리얼라이저"""

    class Meta:
        model = OrderItem
        fields = [
            'drug_code', 'drug_name', 'dosage',
            'frequency', 'duration', 'route', 'instructions'
        ]

from rest_framework import serializers
from .models import Encounter
from apps.patients.models import Patient
from apps.accounts.models import User


class EncounterListSerializer(serializers.ModelSerializer):
    """진료 목록용 Serializer"""

    patient_name = serializers.CharField(source='patient.name', read_only=True)
    patient_number = serializers.CharField(source='patient.patient_number', read_only=True)
    attending_doctor_name = serializers.CharField(source='attending_doctor.name', read_only=True)
    encounter_type_display = serializers.CharField(source='get_encounter_type_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    department_display = serializers.CharField(source='get_department_display', read_only=True)

    class Meta:
        model = Encounter
        fields = [
            'id',
            'patient',
            'patient_name',
            'patient_number',
            'encounter_type',
            'encounter_type_display',
            'status',
            'status_display',
            'attending_doctor',
            'attending_doctor_name',
            'department',
            'department_display',
            'admission_date',
            'discharge_date',
            'chief_complaint',
            'created_at',
        ]
        read_only_fields = ['id', 'created_at']


class EncounterDetailSerializer(serializers.ModelSerializer):
    """진료 상세 정보용 Serializer"""

    patient_name = serializers.CharField(source='patient.name', read_only=True)
    patient_number = serializers.CharField(source='patient.patient_number', read_only=True)
    patient_gender = serializers.CharField(source='patient.gender', read_only=True)
    patient_age = serializers.IntegerField(source='patient.age', read_only=True)
    attending_doctor_name = serializers.CharField(source='attending_doctor.name', read_only=True)
    encounter_type_display = serializers.CharField(source='get_encounter_type_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    department_display = serializers.CharField(source='get_department_display', read_only=True)
    duration_days = serializers.ReadOnlyField()
    is_active = serializers.ReadOnlyField()

    class Meta:
        model = Encounter
        fields = [
            'id',
            'patient',
            'patient_name',
            'patient_number',
            'patient_gender',
            'patient_age',
            'encounter_type',
            'encounter_type_display',
            'status',
            'status_display',
            'attending_doctor',
            'attending_doctor_name',
            'department',
            'department_display',
            'admission_date',
            'discharge_date',
            'duration_days',
            'chief_complaint',
            'primary_diagnosis',
            'secondary_diagnoses',
            'is_active',
            'created_at',
            'updated_at',
        ]
        read_only_fields = [
            'id',
            'duration_days',
            'is_active',
            'created_at',
            'updated_at',
        ]


class EncounterCreateSerializer(serializers.ModelSerializer):
    """진료 등록용 Serializer"""

    class Meta:
        model = Encounter
        fields = [
            'patient',
            'encounter_type',
            'status',
            'attending_doctor',
            'department',
            'admission_date',
            'discharge_date',
            'chief_complaint',
            'primary_diagnosis',
            'secondary_diagnoses',
        ]

    def validate_patient(self, value):
        """환자 유효성 검사"""
        if value.is_deleted:
            raise serializers.ValidationError("삭제된 환자입니다.")
        if value.status != 'active':
            raise serializers.ValidationError("활성 상태가 아닌 환자입니다.")
        return value

    def validate_attending_doctor(self, value):
        """담당 의사 유효성 검사"""
        if value.role.code != 'DOCTOR':
            raise serializers.ValidationError("의사만 담당 의사로 지정할 수 있습니다.")
        return value

    def validate(self, data):
        """전체 유효성 검사"""
        admission_date = data.get('admission_date')
        discharge_date = data.get('discharge_date')

        # 퇴원 일시 = 입원 일시인 경우 입원중으로 간주 (NULL 처리)
        if discharge_date and admission_date:
            if discharge_date == admission_date:
                data['discharge_date'] = None
            elif discharge_date < admission_date:
                raise serializers.ValidationError({
                    'discharge_date': '퇴원 일시는 입원 일시보다 이후여야 합니다.'
                })

        return data


class EncounterUpdateSerializer(serializers.ModelSerializer):
    """진료 정보 수정용 Serializer"""

    class Meta:
        model = Encounter
        fields = [
            'status',
            'attending_doctor',
            'department',
            'admission_date',
            'discharge_date',
            'chief_complaint',
            'primary_diagnosis',
            'secondary_diagnoses',
        ]

    def validate_attending_doctor(self, value):
        """담당 의사 유효성 검사"""
        if value.role.code != 'DOCTOR':
            raise serializers.ValidationError("의사만 담당 의사로 지정할 수 있습니다.")
        return value

    def validate(self, data):
        """전체 유효성 검사"""
        instance = self.instance
        admission_date = data.get('admission_date', instance.admission_date if instance else None)
        discharge_date = data.get('discharge_date')

        # 퇴원 일시 = 입원 일시인 경우 입원중으로 간주 (NULL 처리)
        if discharge_date and admission_date:
            if discharge_date == admission_date:
                data['discharge_date'] = None
            elif discharge_date < admission_date:
                raise serializers.ValidationError({
                    'discharge_date': '퇴원 일시는 입원 일시보다 이후여야 합니다.'
                })

        return data


class EncounterSearchSerializer(serializers.Serializer):
    """진료 검색용 Serializer"""

    q = serializers.CharField(
        required=False,
        allow_blank=True,
        help_text='검색어 (환자명, 환자번호, 주호소)'
    )
    encounter_type = serializers.ChoiceField(
        choices=Encounter.ENCOUNTER_TYPE_CHOICES,
        required=False,
        help_text='진료 유형'
    )
    status = serializers.ChoiceField(
        choices=Encounter.STATUS_CHOICES,
        required=False,
        help_text='진료 상태'
    )
    department = serializers.ChoiceField(
        choices=Encounter.DEPARTMENT_CHOICES,
        required=False,
        help_text='진료과'
    )
    attending_doctor = serializers.IntegerField(
        required=False,
        help_text='담당 의사 ID'
    )
    patient = serializers.IntegerField(
        required=False,
        help_text='환자 ID'
    )
    start_date = serializers.DateField(
        required=False,
        help_text='진료 시작일 (YYYY-MM-DD)'
    )
    end_date = serializers.DateField(
        required=False,
        help_text='진료 종료일 (YYYY-MM-DD)'
    )

    def validate(self, data):
        """날짜 범위 검증"""
        start_date = data.get('start_date')
        end_date = data.get('end_date')

        if start_date and end_date and start_date > end_date:
            raise serializers.ValidationError("시작일은 종료일보다 이전이어야 합니다.")

        return data

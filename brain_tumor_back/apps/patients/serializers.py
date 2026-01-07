from rest_framework import serializers
from .models import Patient
from apps.accounts.models import User


class PatientListSerializer(serializers.ModelSerializer):
    """환자 목록용 Serializer (간단한 정보만)"""

    age = serializers.ReadOnlyField()
    registered_by_name = serializers.CharField(source='registered_by.username', read_only=True)

    class Meta:
        model = Patient
        fields = [
            'id',
            'patient_number',
            'name',
            'birth_date',
            'age',
            'gender',
            'phone',
            'blood_type',
            'status',
            'registered_by_name',
            'created_at',
        ]
        read_only_fields = ['id', 'patient_number', 'created_at']


class PatientDetailSerializer(serializers.ModelSerializer):
    """환자 상세 정보용 Serializer"""

    age = serializers.ReadOnlyField()
    is_active = serializers.ReadOnlyField()
    registered_by_name = serializers.CharField(source='registered_by.username', read_only=True)

    class Meta:
        model = Patient
        fields = [
            'id',
            'patient_number',
            'name',
            'birth_date',
            'age',
            'gender',
            'phone',
            'email',
            'address',
            'ssn',
            'blood_type',
            'allergies',
            'chronic_diseases',
            'status',
            'is_active',
            'registered_by',
            'registered_by_name',
            'created_at',
            'updated_at',
        ]
        read_only_fields = [
            'id',
            'patient_number',
            'age',
            'is_active',
            'registered_by',
            'registered_by_name',
            'created_at',
            'updated_at',
        ]
        extra_kwargs = {
            'ssn': {'write_only': True},  # SSN은 쓰기만 가능, 읽기 시 마스킹 필요
        }

    def validate_phone(self, value):
        """전화번호 형식 검증"""
        import re
        pattern = r'^\d{2,3}-\d{3,4}-\d{4}$'
        if not re.match(pattern, value):
            raise serializers.ValidationError("전화번호 형식이 올바르지 않습니다. (예: 010-1234-5678)")
        return value

    def validate_ssn(self, value):
        """주민등록번호 검증 (간단한 형식 체크)"""
        import re
        # 하이픈 제거
        ssn_cleaned = value.replace('-', '')

        # 13자리 숫자인지 확인
        if not re.match(r'^\d{13}$', ssn_cleaned):
            raise serializers.ValidationError("주민등록번호는 13자리 숫자여야 합니다.")

        # 중복 체크 (수정 시 제외)
        instance = self.instance
        if Patient.objects.filter(ssn=value).exclude(pk=instance.pk if instance else None).exists():
            raise serializers.ValidationError("이미 등록된 주민등록번호입니다.")

        return value

    def validate_allergies(self, value):
        """알레르기 데이터 검증"""
        if not isinstance(value, list):
            raise serializers.ValidationError("알레르기는 배열 형식이어야 합니다.")
        return value

    def validate_chronic_diseases(self, value):
        """기저질환 데이터 검증"""
        if not isinstance(value, list):
            raise serializers.ValidationError("기저질환은 배열 형식이어야 합니다.")
        return value


class PatientCreateSerializer(serializers.ModelSerializer):
    """환자 등록용 Serializer"""

    class Meta:
        model = Patient
        fields = [
            'name',
            'birth_date',
            'gender',
            'phone',
            'email',
            'address',
            'ssn',
            'blood_type',
            'allergies',
            'chronic_diseases',
        ]

    def validate_phone(self, value):
        """전화번호 형식 검증"""
        import re
        pattern = r'^\d{2,3}-\d{3,4}-\d{4}$'
        if not re.match(pattern, value):
            raise serializers.ValidationError("전화번호 형식이 올바르지 않습니다. (예: 010-1234-5678)")
        return value

    def validate_ssn(self, value):
        """주민등록번호 검증"""
        import re
        ssn_cleaned = value.replace('-', '')

        if not re.match(r'^\d{13}$', ssn_cleaned):
            raise serializers.ValidationError("주민등록번호는 13자리 숫자여야 합니다.")

        if Patient.objects.filter(ssn=value).exists():
            raise serializers.ValidationError("이미 등록된 주민등록번호입니다.")

        return value

    def create(self, validated_data):
        """환자 생성 (등록자 정보 자동 추가)"""
        request = self.context.get('request')
        if request and request.user:
            validated_data['registered_by'] = request.user
        return super().create(validated_data)


class PatientUpdateSerializer(serializers.ModelSerializer):
    """환자 정보 수정용 Serializer"""

    class Meta:
        model = Patient
        fields = [
            'name',
            'phone',
            'email',
            'address',
            'blood_type',
            'allergies',
            'chronic_diseases',
            'status',
        ]

    def validate_phone(self, value):
        """전화번호 형식 검증"""
        import re
        pattern = r'^\d{2,3}-\d{3,4}-\d{4}$'
        if not re.match(pattern, value):
            raise serializers.ValidationError("전화번호 형식이 올바르지 않습니다. (예: 010-1234-5678)")
        return value


class PatientSearchSerializer(serializers.Serializer):
    """환자 검색용 Serializer"""

    q = serializers.CharField(
        required=False,
        allow_blank=True,
        help_text='검색어 (이름, 환자번호, 전화번호)'
    )
    status = serializers.ChoiceField(
        choices=Patient.STATUS_CHOICES,
        required=False,
        help_text='환자 상태'
    )
    gender = serializers.ChoiceField(
        choices=Patient.GENDER_CHOICES,
        required=False,
        help_text='성별'
    )
    start_date = serializers.DateField(
        required=False,
        help_text='등록일 시작 (YYYY-MM-DD)'
    )
    end_date = serializers.DateField(
        required=False,
        help_text='등록일 종료 (YYYY-MM-DD)'
    )

    def validate(self, data):
        """날짜 범위 검증"""
        start_date = data.get('start_date')
        end_date = data.get('end_date')

        if start_date and end_date and start_date > end_date:
            raise serializers.ValidationError("시작일은 종료일보다 이전이어야 합니다.")

        return data

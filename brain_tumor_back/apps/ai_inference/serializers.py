from rest_framework import serializers
from django.utils import timezone
from .models import AIModel, AIInferenceRequest, AIInferenceResult, AIInferenceLog
from apps.patients.models import Patient
from apps.ocs.models import OCS


class AIModelSerializer(serializers.ModelSerializer):
    """AI 모델 시리얼라이저"""

    class Meta:
        model = AIModel
        fields = [
            'id', 'code', 'name', 'description',
            'ocs_sources', 'required_keys', 'version',
            'is_active', 'config', 'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']


class AIModelListSerializer(serializers.ModelSerializer):
    """AI 모델 목록용 시리얼라이저"""

    class Meta:
        model = AIModel
        fields = ['id', 'code', 'name', 'description', 'ocs_sources', 'is_active']


class AIInferenceResultSerializer(serializers.ModelSerializer):
    """AI 추론 결과 시리얼라이저"""
    reviewed_by_name = serializers.CharField(source='reviewed_by.name', read_only=True, allow_null=True)
    review_status_display = serializers.CharField(source='get_review_status_display', read_only=True)

    class Meta:
        model = AIInferenceResult
        fields = [
            'id', 'result_data', 'confidence_score', 'visualization_paths',
            'reviewed_by', 'reviewed_by_name', 'review_status', 'review_status_display',
            'review_comment', 'reviewed_at', 'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']


class AIInferenceLogSerializer(serializers.ModelSerializer):
    """AI 추론 로그 시리얼라이저"""
    action_display = serializers.CharField(source='get_action_display', read_only=True)

    class Meta:
        model = AIInferenceLog
        fields = ['id', 'action', 'action_display', 'message', 'details', 'created_at']
        read_only_fields = ['created_at']


class AIInferenceRequestListSerializer(serializers.ModelSerializer):
    """AI 추론 요청 목록용 시리얼라이저"""
    patient_name = serializers.CharField(source='patient.name', read_only=True)
    patient_number = serializers.CharField(source='patient.patient_number', read_only=True)
    model_code = serializers.CharField(source='model.code', read_only=True)
    model_name = serializers.CharField(source='model.name', read_only=True)
    requested_by_name = serializers.CharField(source='requested_by.name', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    priority_display = serializers.CharField(source='get_priority_display', read_only=True)
    has_result = serializers.SerializerMethodField()

    class Meta:
        model = AIInferenceRequest
        fields = [
            'id', 'request_id', 'patient', 'patient_name', 'patient_number',
            'model', 'model_code', 'model_name',
            'requested_by', 'requested_by_name',
            'status', 'status_display', 'priority', 'priority_display',
            'requested_at', 'completed_at', 'has_result'
        ]

    def get_has_result(self, obj):
        return hasattr(obj, 'result') and obj.result is not None


class AIInferenceRequestDetailSerializer(serializers.ModelSerializer):
    """AI 추론 요청 상세 시리얼라이저"""
    patient_name = serializers.CharField(source='patient.name', read_only=True)
    patient_number = serializers.CharField(source='patient.patient_number', read_only=True)
    model_code = serializers.CharField(source='model.code', read_only=True)
    model_name = serializers.CharField(source='model.name', read_only=True)
    requested_by_name = serializers.CharField(source='requested_by.name', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    priority_display = serializers.CharField(source='get_priority_display', read_only=True)
    result = AIInferenceResultSerializer(read_only=True)
    logs = AIInferenceLogSerializer(many=True, read_only=True)
    processing_time = serializers.FloatField(read_only=True)

    class Meta:
        model = AIInferenceRequest
        fields = [
            'id', 'request_id', 'patient', 'patient_name', 'patient_number',
            'model', 'model_code', 'model_name',
            'requested_by', 'requested_by_name',
            'ocs_references', 'input_data',
            'status', 'status_display', 'priority', 'priority_display',
            'requested_at', 'started_at', 'completed_at', 'processing_time',
            'error_message', 'result', 'logs',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['request_id', 'created_at', 'updated_at']


class AIInferenceRequestCreateSerializer(serializers.ModelSerializer):
    """AI 추론 요청 생성 시리얼라이저"""
    patient_id = serializers.IntegerField(write_only=True)
    model_code = serializers.CharField(write_only=True)
    ocs_ids = serializers.ListField(
        child=serializers.IntegerField(),
        write_only=True,
        required=False,
        help_text='사용할 OCS ID 목록 (미지정 시 자동 선택)'
    )

    class Meta:
        model = AIInferenceRequest
        fields = ['patient_id', 'model_code', 'priority', 'ocs_ids']

    def validate_patient_id(self, value):
        try:
            Patient.objects.get(id=value)
        except Patient.DoesNotExist:
            raise serializers.ValidationError('존재하지 않는 환자입니다.')
        return value

    def validate_model_code(self, value):
        try:
            AIModel.objects.get(code=value, is_active=True)
        except AIModel.DoesNotExist:
            raise serializers.ValidationError('존재하지 않거나 비활성화된 모델입니다.')
        return value

    def create(self, validated_data):
        patient_id = validated_data.pop('patient_id')
        model_code = validated_data.pop('model_code')
        ocs_ids = validated_data.pop('ocs_ids', None)

        patient = Patient.objects.get(id=patient_id)
        model = AIModel.objects.get(code=model_code)
        user = self.context['request'].user

        # OCS 데이터 수집
        ocs_references, input_data = self._collect_input_data(patient, model, ocs_ids)

        request = AIInferenceRequest.objects.create(
            patient=patient,
            model=model,
            requested_by=user,
            ocs_references=ocs_references,
            input_data=input_data,
            **validated_data
        )

        # 로그 생성
        AIInferenceLog.objects.create(
            inference_request=request,
            action=AIInferenceLog.Action.CREATED,
            message=f'{user.name}님이 {model.name} 추론을 요청했습니다.',
            details={
                'patient_id': patient.id,
                'model_code': model.code,
                'ocs_count': len(ocs_references)
            }
        )

        return request

    def _collect_input_data(self, patient, model, ocs_ids=None):
        """환자의 OCS에서 모델 입력 데이터 수집"""
        ocs_references = []
        input_data = {}

        # 모델이 요구하는 OCS 소스 조회
        for source in model.ocs_sources:
            ocs_queryset = OCS.objects.filter(
                patient=patient,
                job_role=source,
                ocs_status='CONFIRMED'
            ).order_by('-confirmed_at')

            if ocs_ids:
                ocs_queryset = ocs_queryset.filter(id__in=ocs_ids)

            # 최신 확정된 OCS 선택
            ocs = ocs_queryset.first()
            if ocs:
                ocs_references.append(ocs.id)
                # worker_result에서 필요한 키 추출
                required_keys = model.required_keys.get(source, [])
                for key in required_keys:
                    value = self._get_nested_value(ocs.worker_result, key)
                    if value is not None:
                        input_data[key] = value

        return ocs_references, input_data

    def _get_nested_value(self, data, key):
        """
        중첩 딕셔너리에서 값 추출 (확장된 로직)

        특수 케이스 처리:
        - dicom.T1, dicom.T2, dicom.T1C, dicom.FLAIR:
          dicom.series 배열에서 series_type/seriesType 매칭
        - 일반 키: 기존 dot notation 방식
        """
        if not data:
            return None

        keys = key.split('.')

        # 특수 케이스: dicom.시리즈타입 (T1, T2, T1C, FLAIR)
        if len(keys) == 2 and keys[0] == 'dicom':
            series_type = keys[1].upper()  # T1, T2, T1C, FLAIR
            dicom_data = data.get('dicom', {})
            series_list = dicom_data.get('series', [])

            # series 배열에서 해당 series_type 찾기
            for series in series_list:
                # series_type 또는 seriesType 키 확인
                s_type = series.get('series_type', series.get('seriesType', '')).upper()
                if s_type == series_type:
                    return series  # 해당 시리즈 데이터 반환

            return None

        # 일반 케이스: 기존 dot notation
        value = data
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return None
        return value


class DataValidationSerializer(serializers.Serializer):
    """데이터 검증 요청 시리얼라이저"""
    patient_id = serializers.IntegerField()
    model_code = serializers.CharField()

    def validate_patient_id(self, value):
        try:
            Patient.objects.get(id=value)
        except Patient.DoesNotExist:
            raise serializers.ValidationError('존재하지 않는 환자입니다.')
        return value

    def validate_model_code(self, value):
        try:
            AIModel.objects.get(code=value, is_active=True)
        except AIModel.DoesNotExist:
            raise serializers.ValidationError('존재하지 않거나 비활성화된 모델입니다.')
        return value


class ReviewRequestSerializer(serializers.Serializer):
    """결과 검토 요청 시리얼라이저"""
    review_status = serializers.ChoiceField(choices=['approved', 'rejected'])
    review_comment = serializers.CharField(required=False, allow_blank=True)

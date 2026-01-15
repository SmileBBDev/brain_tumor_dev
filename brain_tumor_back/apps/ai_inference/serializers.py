from rest_framework import serializers
from .models import AIInference


class InferenceRequestSerializer(serializers.Serializer):
    """추론 요청 직렬화"""
    ocs_id = serializers.IntegerField(help_text='OCS ID')
    mode = serializers.ChoiceField(
        choices=['manual', 'auto'],
        default='manual',
        help_text='추론 모드'
    )


class InferenceCallbackSerializer(serializers.Serializer):
    """FastAPI 콜백 직렬화"""
    job_id = serializers.CharField()
    status = serializers.ChoiceField(choices=['completed', 'failed'])
    result_data = serializers.JSONField(required=False, default=dict)
    error_message = serializers.CharField(required=False, allow_null=True)


class AIInferenceSerializer(serializers.ModelSerializer):
    """AI 추론 결과 직렬화"""
    patient_name = serializers.CharField(source='patient.name', read_only=True)
    patient_number = serializers.CharField(source='patient.patient_number', read_only=True)

    class Meta:
        model = AIInference
        fields = [
            'id', 'job_id', 'model_type', 'status', 'mode',
            'patient', 'patient_name', 'patient_number',
            'mri_ocs', 'rna_ocs', 'protein_ocs',
            'result_data', 'error_message',
            'created_at', 'completed_at'
        ]
        read_only_fields = ['job_id', 'created_at', 'completed_at']

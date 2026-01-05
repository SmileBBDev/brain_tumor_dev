"""
FHIR Serializers

FHIR 리소스 및 동기화 큐를 위한 Serializer
"""
from rest_framework import serializers
from .models import FHIRResourceMap, FHIRSyncQueue


class FHIRResourceMapSerializer(serializers.ModelSerializer):
    """FHIR Resource Map Serializer"""

    class Meta:
        model = FHIRResourceMap
        fields = [
            'map_id',
            'resource_type',
            'cdss_id',
            'fhir_id',
            'fhir_server_url',
            'last_synced_at',
            'created_at',
            'updated_at'
        ]
        read_only_fields = ['map_id', 'created_at', 'updated_at']


class FHIRSyncQueueSerializer(serializers.ModelSerializer):
    """FHIR Sync Queue Serializer"""

    resource_map_detail = FHIRResourceMapSerializer(source='resource_map', read_only=True)

    class Meta:
        model = FHIRSyncQueue
        fields = [
            'queue_id',
            'resource_map',
            'resource_map_detail',
            'operation',
            'status',
            'priority',
            'retry_count',
            'max_retries',
            'error_message',
            'payload',
            'scheduled_at',
            'started_at',
            'completed_at',
            'created_at',
            'updated_at'
        ]
        read_only_fields = [
            'queue_id',
            'status',
            'retry_count',
            'started_at',
            'completed_at',
            'created_at',
            'updated_at'
        ]


class FHIRSyncRequestSerializer(serializers.Serializer):
    """FHIR 동기화 요청 Serializer"""

    resource_type = serializers.ChoiceField(
        choices=['Patient', 'Encounter', 'Observation', 'DiagnosticReport'],
        help_text='FHIR 리소스 타입'
    )
    cdss_id = serializers.CharField(
        max_length=100,
        help_text='CDSS 내부 리소스 ID'
    )
    operation = serializers.ChoiceField(
        choices=['create', 'update', 'delete'],
        default='create',
        help_text='동기화 작업 타입'
    )
    priority = serializers.IntegerField(
        default=5,
        min_value=1,
        max_value=10,
        help_text='우선순위 (1=highest, 10=lowest)'
    )

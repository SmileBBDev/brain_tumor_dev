"""
FHIR Models

HL7 FHIR R4 표준 기반 의료정보 교환
"""
from django.db import models
from django.utils import timezone


class FHIRResourceMap(models.Model):
    """
    CDSS ID ↔ FHIR Resource ID 매핑 테이블

    CDSS 내부 리소스와 외부 FHIR 서버의 리소스를 매핑합니다.
    """
    RESOURCE_TYPES = [
        ('Patient', 'Patient'),
        ('Encounter', 'Encounter'),
        ('Observation', 'Observation'),
        ('DiagnosticReport', 'DiagnosticReport'),
        ('MedicationRequest', 'MedicationRequest'),
        ('ServiceRequest', 'ServiceRequest'),
        ('Condition', 'Condition'),
        ('ImagingStudy', 'ImagingStudy'),
        ('Procedure', 'Procedure'),
    ]

    map_id = models.AutoField(primary_key=True)
    resource_type = models.CharField(
        max_length=50,
        choices=RESOURCE_TYPES,
        help_text='FHIR 리소스 타입'
    )
    cdss_id = models.CharField(
        max_length=100,
        help_text='CDSS 내부 리소스 ID'
    )
    fhir_id = models.CharField(
        max_length=100,
        help_text='FHIR 서버 리소스 ID'
    )
    fhir_server_url = models.URLField(
        max_length=500,
        null=True,
        blank=True,
        help_text='HAPI FHIR 서버 URL'
    )
    last_synced_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text='마지막 동기화 시간'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'fhir_resource_map'
        unique_together = [['resource_type', 'cdss_id'], ['resource_type', 'fhir_id']]
        indexes = [
            models.Index(fields=['resource_type', 'cdss_id']),
            models.Index(fields=['resource_type', 'fhir_id']),
        ]
        verbose_name = 'FHIR Resource Map'
        verbose_name_plural = 'FHIR Resource Maps'

    def __str__(self):
        return f"{self.resource_type}: {self.cdss_id} → {self.fhir_id}"


class FHIRSyncQueue(models.Model):
    """
    FHIR 동기화 작업 큐

    CDSS → FHIR 서버로 데이터 동기화 작업을 관리합니다.
    """
    SYNC_STATUS = [
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    ]

    SYNC_OPERATIONS = [
        ('create', 'Create'),
        ('update', 'Update'),
        ('delete', 'Delete'),
    ]

    queue_id = models.AutoField(primary_key=True)
    resource_map = models.ForeignKey(
        FHIRResourceMap,
        on_delete=models.CASCADE,
        related_name='sync_queue',
        help_text='연결된 FHIR 리소스 맵'
    )
    operation = models.CharField(
        max_length=20,
        choices=SYNC_OPERATIONS,
        help_text='동기화 작업 타입'
    )
    status = models.CharField(
        max_length=20,
        choices=SYNC_STATUS,
        default='pending',
        help_text='동기화 상태'
    )
    priority = models.IntegerField(
        default=5,
        help_text='우선순위 (1=highest, 10=lowest)'
    )
    retry_count = models.IntegerField(
        default=0,
        help_text='재시도 횟수'
    )
    max_retries = models.IntegerField(
        default=3,
        help_text='최대 재시도 횟수'
    )
    error_message = models.TextField(
        null=True,
        blank=True,
        help_text='에러 메시지'
    )
    payload = models.JSONField(
        null=True,
        blank=True,
        help_text='동기화할 데이터 (FHIR Resource JSON)'
    )
    scheduled_at = models.DateTimeField(
        default=timezone.now,
        help_text='예정 실행 시간'
    )
    started_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text='실행 시작 시간'
    )
    completed_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text='완료 시간'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'fhir_sync_queue'
        indexes = [
            models.Index(fields=['status', 'priority', 'scheduled_at']),
            models.Index(fields=['resource_map', 'status']),
        ]
        ordering = ['priority', 'scheduled_at']
        verbose_name = 'FHIR Sync Queue'
        verbose_name_plural = 'FHIR Sync Queues'

    def __str__(self):
        return f"{self.operation} {self.resource_map.resource_type} ({self.status})"

    def mark_as_processing(self):
        """작업 시작 표시"""
        self.status = 'processing'
        self.started_at = timezone.now()
        self.save(update_fields=['status', 'started_at', 'updated_at'])

    def mark_as_completed(self):
        """작업 완료 표시"""
        self.status = 'completed'
        self.completed_at = timezone.now()
        self.save(update_fields=['status', 'completed_at', 'updated_at'])

    def mark_as_failed(self, error_message: str):
        """작업 실패 표시"""
        self.status = 'failed'
        self.error_message = error_message
        self.retry_count += 1
        self.save(update_fields=['status', 'error_message', 'retry_count', 'updated_at'])

    def can_retry(self) -> bool:
        """재시도 가능 여부"""
        return self.retry_count < self.max_retries and self.status == 'failed'

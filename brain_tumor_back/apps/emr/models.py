"""
EMR 모델 정의

공통 모델은 apps.common.models에서 import하여 사용
EMR 앱 전용 모델만 이곳에 정의
"""

from django.db import models
from django.utils import timezone
import uuid
from django.conf import settings

# 공통 모델 import (하위 호환성을 위해 별칭 제공)
from apps.common.models import (
    Patient as PatientCache,  # 기존 이름으로 별칭
    Encounter,
    EncounterDiagnosis,
    Order,
    OrderItem
)

# 하위 호환성을 위한 export
__all__ = ['PatientCache', 'Encounter', 'EncounterDiagnosis', 'Order', 'OrderItem', 'SyncOutbox']


class SyncOutbox(models.Model):
    """
    외부 시스템 동기화 Outbox 테이블

    Transactional Outbox Pattern:
    - Django MySQL에 데이터 저장 시, 동기화 작업도 함께 저장
    - Celery Worker가 비동기로 처리
    - 재시도 로직으로 데이터 유실 방지
    """

    ENTITY_TYPE_CHOICES = [
        ('patient', 'Patient'),
        ('encounter', 'Encounter'),
        ('order', 'Order'),
    ]

    OPERATION_CHOICES = [
        ('create', 'Create'),
        ('update', 'Update'),
        ('delete', 'Delete'),
    ]

    TARGET_SYSTEM_CHOICES = [
        ('openemr', 'OpenEMR'),
        ('fhir', 'FHIR Server'),
    ]

    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('done', 'Done'),
        ('failed', 'Failed'),
    ]

    # Primary Key
    outbox_id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        help_text="Outbox 레코드 고유 ID"
    )

    # 동기화 대상 엔티티
    entity_type = models.CharField(
        max_length=20,
        choices=ENTITY_TYPE_CHOICES,
        help_text="동기화 대상 엔티티 타입"
    )
    entity_id = models.CharField(
        max_length=100,
        help_text="동기화 대상 엔티티 ID (patient_id, encounter_id 등)"
    )

    # 작업 정보
    operation = models.CharField(
        max_length=10,
        choices=OPERATION_CHOICES,
        help_text="작업 타입 (create, update, delete)"
    )
    target_system = models.CharField(
        max_length=20,
        choices=TARGET_SYSTEM_CHOICES,
        help_text="동기화 대상 시스템"
    )

    # 페이로드 (JSON)
    payload = models.JSONField(
        help_text="동기화할 데이터 (FHIR 리소스 등)"
    )

    # 상태 및 재시도
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending',
        db_index=True,
        help_text="처리 상태"
    )
    retry_count = models.IntegerField(
        default=0,
        help_text="재시도 횟수"
    )
    max_retries = models.IntegerField(
        default=5,
        help_text="최대 재시도 횟수"
    )

    # 에러 정보
    error_message = models.TextField(
        blank=True,
        null=True,
        help_text="에러 메시지 (실패 시)"
    )
    last_error_at = models.DateTimeField(
        blank=True,
        null=True,
        help_text="마지막 에러 발생 시간"
    )

    # 타임스탬프
    created_at = models.DateTimeField(
        auto_now_add=True,
        db_index=True,
        help_text="생성 시간"
    )
    processed_at = models.DateTimeField(
        blank=True,
        null=True,
        help_text="처리 완료 시간"
    )
    next_retry_at = models.DateTimeField(
        blank=True,
        null=True,
        db_index=True,
        help_text="다음 재시도 예정 시간 (Exponential Backoff)"
    )

    class Meta:
        db_table = 'emr_sync_outbox'
        verbose_name = '동기화 Outbox'
        verbose_name_plural = '동기화 Outbox 목록'
        ordering = ['created_at']
        indexes = [
            models.Index(fields=['status', 'next_retry_at'], name='idx_sync_status_retry'),
            models.Index(fields=['entity_type', 'entity_id'], name='idx_sync_entity'),
            models.Index(fields=['target_system', 'status'], name='idx_sync_target'),
        ]

    def __str__(self):
        return f"{self.outbox_id} - {self.entity_type}:{self.entity_id} [{self.status}]"

    @property
    def is_retryable(self):
        """재시도 가능 여부"""
        return self.retry_count < self.max_retries and self.status != 'done'

    def calculate_next_retry(self):
        """
        지수 백오프(Exponential Backoff) 계산

        재시도 간격:
        - 1차: 1분 후
        - 2차: 2분 후
        - 3차: 4분 후
        - 4차: 8분 후
        - 5차: 16분 후
        """
        from datetime import timedelta
        if not self.is_retryable:
            return None

        backoff_minutes = 2 ** self.retry_count  # 1, 2, 4, 8, 16...
        return timezone.now() + timedelta(minutes=backoff_minutes)

    def mark_as_processing(self):
        """처리 중으로 상태 변경"""
        self.status = 'processing'
        self.save(update_fields=['status'])

    def mark_as_done(self):
        """처리 완료로 상태 변경"""
        self.status = 'done'
        self.processed_at = timezone.now()
        self.error_message = None
        self.save(update_fields=['status', 'processed_at', 'error_message'])

    def mark_as_failed(self, error_msg: str):
        """
        실패로 상태 변경 및 재시도 예약

        Args:
            error_msg: 에러 메시지
        """
        self.retry_count += 1
        self.error_message = error_msg
        self.last_error_at = timezone.now()

        if self.is_retryable:
            # 재시도 가능 - 다음 재시도 시간 계산
            self.status = 'failed'
            self.next_retry_at = self.calculate_next_retry()
        else:
            # 최대 재시도 초과 - 영구 실패
            self.status = 'failed'
            self.next_retry_at = None

        self.save(update_fields=[
            'status', 'retry_count', 'error_message',
            'last_error_at', 'next_retry_at'
        ])

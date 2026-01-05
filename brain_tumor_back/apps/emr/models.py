"""
EMR 모델 정의

Django MySQL에 저장되는 환자 기본 정보 (캐시)
상세 정보는 OpenEMR에 저장되고 FHIR를 통해 동기화
"""

from django.db import models
from django.utils import timezone
import uuid
from django.conf import settings

class PatientCache(models.Model):
    """
    환자 기본 정보 캐시 테이블

    - Django MySQL에 일반 정보 저장
    - OpenEMR에 상세 정보 저장
    - FHIR API를 통해 양방향 동기화
    """
    GENDER_CHOICES = [
        ('male', '남성'),
        ('female', '여성'),
        ('other', '기타'),
        ('unknown', '미상'),
    ]

    patient_id = models.CharField(
        max_length=20,
        primary_key=True,
        help_text="환자 ID (예: P-2024-001234)"
    )
    family_name = models.CharField(max_length=50, help_text="성")
    given_name = models.CharField(max_length=50, help_text="이름")
    birth_date = models.DateField(help_text="생년월일")
    gender = models.CharField(max_length=10, choices=GENDER_CHOICES, help_text="성별")
    phone = models.CharField(max_length=20, blank=True, null=True, help_text="전화번호")
    email = models.EmailField(max_length=100, blank=True, null=True, help_text="이메일")
    address = models.TextField(blank=True, null=True, help_text="주소")
    ssn = models.CharField(
        max_length=13,
        unique=True,
        blank=True,
        null=True,
        help_text="주민등록번호 (13자리 숫자)"
    )

    # JSON 필드
    emergency_contact = models.JSONField(
        blank=True,
        null=True,
        help_text="응급 연락처 정보 {'name': '...', 'relationship': '...', 'phone': '...'}"
    )
    allergies = models.JSONField(
        blank=True,
        null=True,
        help_text="알레르기 목록 ['페니실린', '땅콩']"
    )

    blood_type = models.CharField(
        max_length=5,
        blank=True,
        null=True,
        help_text="혈액형 (예: A+, B-, O+, AB-)"
    )

    # OpenEMR 동기화
    openemr_patient_id = models.CharField(
        max_length=100,
        unique=True,
        blank=True,
        null=True,
        help_text="OpenEMR의 환자 ID (FHIR Patient resource ID)"
    )
    last_synced_at = models.DateTimeField(
        blank=True,
        null=True,
        help_text="OpenEMR과 마지막 동기화 시간"
    )

    # HAPI FHIR 동기화
    fhir_id = models.CharField(
        max_length=64,
        blank=True,
        null=True,
        unique=True,
        help_text="HAPI FHIR Patient resource ID"
    )

    # 타임스탬프 및 버전
    created_at = models.DateTimeField(auto_now_add=True, help_text="생성 시간")
    updated_at = models.DateTimeField(auto_now=True, help_text="수정 시간")
    version = models.IntegerField(default=1, help_text="낙관적 락을 위한 버전 필드")

    class Meta:
        db_table = 'emr_patient_cache'
        verbose_name = '환자 캐시'
        verbose_name_plural = '환자 캐시 목록'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['family_name', 'given_name'], name='idx_patient_name'),
            models.Index(fields=['birth_date'], name='idx_patient_birth'),
            models.Index(fields=['phone'], name='idx_patient_phone'),
            models.Index(fields=['ssn'], name='idx_patient_ssn'),  # 주민등록번호 검색 최적화
        ]

    def __str__(self):
        return f"{self.patient_id} - {self.family_name}{self.given_name}"

    @property
    def full_name(self):
        """전체 이름 반환"""
        return f"{self.family_name}{self.given_name}"

    @property
    def is_synced(self):
        """OpenEMR과 동기화 여부"""
        return self.openemr_patient_id is not None


class Encounter(models.Model):
    """
    진료 기록 (Encounter)
    """
    ENCOUNTER_TYPE_CHOICES = [
        ('outpatient', '외래'),
        ('emergency', '응급'),
        ('inpatient', '입원'),
        ('discharge', '퇴원'),
    ]

    STATUS_CHOICES = [
        ('scheduled', '예정'),
        ('in_progress', '진행중'),
        ('completed', '완료'),
        ('cancelled', '취소'),
    ]

    encounter_id = models.CharField(
        max_length=20,
        primary_key=True,
        help_text="진료 ID (예: E-2025-005678)"
    )
    patient = models.ForeignKey(
        PatientCache,
        on_delete=models.CASCADE,
        related_name='encounters',
        db_column='patient_id',
        help_text="환자"
    )
    doctor = models.ForeignKey(
        # 'acct.User',
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='encounters',
        help_text="의사 (User FK)"
    )

    encounter_type = models.CharField(
        max_length=20,
        choices=ENCOUNTER_TYPE_CHOICES,
        help_text="진료 유형"
    )
    department = models.CharField(max_length=100, help_text="진료 부서")
    chief_complaint = models.TextField(blank=True, null=True, help_text="주 호소")
    diagnosis = models.TextField(blank=True, null=True, help_text="진단")
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='scheduled',
        help_text="진료 상태"
    )

    encounter_date = models.DateTimeField(help_text="진료 일시")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    version = models.IntegerField(default=1, help_text="낙관적 락을 위한 버전 필드")

    # HAPI FHIR 동기화
    fhir_id = models.CharField(
        max_length=64,
        blank=True,
        null=True,
        unique=True,
        help_text="HAPI FHIR Encounter resource ID"
    )

    class Meta:
        db_table = 'emr_encounters'
        verbose_name = '진료 기록'
        verbose_name_plural = '진료 기록 목록'
        ordering = ['-encounter_date']
        indexes = [
            models.Index(fields=['patient', 'encounter_date'], name='idx_patient_encounter'),
            models.Index(fields=['doctor', 'encounter_date'], name='idx_doctor_encounter'),
            models.Index(fields=['status'], name='idx_encounter_status'),
        ]

    def __str__(self):
        return f"{self.encounter_id} - {self.patient.full_name} ({self.encounter_date})"


class EncounterDiagnosis(models.Model):
    """
    진료별 진단 내역 (DiagnosisMaster 연동)
    """
    encounter = models.ForeignKey(
        Encounter,
        on_delete=models.CASCADE,
        related_name='diagnoses',
        db_column='encounter_id',
        help_text="진료 기록"
    )
    diag_code = models.CharField(max_length=20, help_text="질병 코드 (ICD-10/KCD)")
    diagnosis_name = models.CharField(max_length=255, help_text="진단명 (한글/영문)")
    priority = models.IntegerField(default=1, help_text="진단 우선순위 (1: 주진단, 2 이상: 부진단)")
    comments = models.TextField(blank=True, null=True, help_text="진단 상세 설명/메모")
    version = models.IntegerField(default=1, help_text="낙관적 락을 위한 버전 필드")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'emr_encounter_diagnoses'
        verbose_name = '진료 진단'
        verbose_name_plural = '진료 진단 목록'
        ordering = ['priority', 'created_at']

    def __str__(self):
        return f"[{self.diag_code}] {self.diagnosis_name}"

    @property
    def master_info(self):
        """진단 마스터 데이터 조회 (OCS 연동)"""
        from ocs.models import DiagnosisMaster
        try:
            return DiagnosisMaster.objects.get(diag_code=self.diag_code)
        except (DiagnosisMaster.DoesNotExist, AttributeError):
            return None


class Order(models.Model):
    """
    OCS 처방 주문
    """
    ORDER_TYPE_CHOICES = [
        ('medication', '약물'),
        ('lab', '검사'),
        ('radiology', '영상'),
        ('procedure', '시술'),
    ]

    URGENCY_CHOICES = [
        ('routine', '일반'),
        ('urgent', '긴급'),
        ('stat', '즉시'),
    ]

    STATUS_CHOICES = [
        ('pending', '대기'),
        ('approved', '승인'),
        ('in_progress', '진행중'),
        ('completed', '완료'),
        ('cancelled', '취소'),
    ]

    order_id = models.CharField(
        max_length=20,
        primary_key=True,
        help_text="처방 ID (예: O-2025-009876)"
    )
    patient = models.ForeignKey(
        PatientCache,
        on_delete=models.CASCADE,
        related_name='orders',
        db_column='patient_id',
        help_text="환자"
    )
    encounter = models.ForeignKey(
        Encounter,
        on_delete=models.CASCADE,
        related_name='orders',
        db_column='encounter_id',
        blank=True,
        null=True,
        help_text="진료 기록"
    )

    ordered_by = models.ForeignKey(
        # 'acct.User',
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='orders_placed',
        db_column='ordered_by',
        help_text="처방 의사 (User FK)"
    )
    order_type = models.CharField(
        max_length=50,
        choices=ORDER_TYPE_CHOICES,
        help_text="처방 유형"
    )
    urgency = models.CharField(
        max_length=20,
        choices=URGENCY_CHOICES,
        default='routine',
        help_text="긴급도"
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending',
        help_text="처방 상태"
    )
    notes = models.TextField(blank=True, null=True, help_text="처방 메모")

    ordered_at = models.DateTimeField(auto_now_add=True, help_text="처방 시간")
    executed_at = models.DateTimeField(blank=True, null=True, help_text="실행 시간")
    version = models.IntegerField(default=1, help_text="낙관적 락을 위한 버전 필드")
    executed_by = models.ForeignKey(
        # 'acct.User',
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='orders_executed',
        db_column='executed_by',
        help_text="실행자 (User FK)"
    )

    # HAPI FHIR 동기화
    fhir_id = models.CharField(
        max_length=64,
        blank=True,
        null=True,
        unique=True,
        help_text="HAPI FHIR MedicationRequest resource ID"
    )

    class Meta:
        db_table = 'ocs_orders'
        verbose_name = '처방'
        verbose_name_plural = '처방 목록'
        ordering = ['-ordered_at']
        indexes = [
            models.Index(fields=['patient', 'ordered_at'], name='idx_patient_order'),
            models.Index(fields=['ordered_by', 'ordered_at'], name='idx_doctor_order'),
            models.Index(fields=['status'], name='idx_order_status'),
            models.Index(fields=['order_type'], name='idx_order_type'),
            models.Index(fields=['status', 'order_type'], name='idx_order_status_type'),  # 복합 인덱스: 상태+유형별 검색 최적화
        ]

    def __str__(self):
        return f"{self.order_id} - {self.patient.full_name} ({self.order_type})"


class OrderItem(models.Model):
    """
    처방 항목 (약물 상세)
    """
    item_id = models.CharField(
        max_length=20,
        primary_key=True,
        help_text="처방 항목 ID (예: OI-001)"
    )
    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        related_name='items',
        db_column='order_id',
        help_text="처방"
    )

    drug_code = models.CharField(max_length=50, blank=True, null=True, help_text="약물 코드")
    drug_name = models.CharField(max_length=200, help_text="약물명")
    dosage = models.CharField(max_length=50, help_text="용량 (예: 1정)")
    frequency = models.CharField(max_length=50, help_text="횟수 (예: 1일 1회)")
    duration = models.CharField(max_length=20, help_text="기간 (예: 7일)")
    route = models.CharField(max_length=50, help_text="투여 경로 (예: 경구)")
    instructions = models.TextField(blank=True, null=True, help_text="복용 지시사항")
    version = models.IntegerField(default=1, help_text="낙관적 락을 위한 버전 필드")

    class Meta:
        db_table = 'ocs_order_items'
        verbose_name = '처방 항목'
        verbose_name_plural = '처방 항목 목록'

    def __str__(self):
        return f"{self.item_id} - {self.drug_name}"

    @property
    def master_info(self):
        """약물 마스터 데이터 조회 (OCS 연동)"""
        from ocs.models import MedicationMaster
        try:
            return MedicationMaster.objects.get(drug_code=self.drug_code)
        except (MedicationMaster.DoesNotExist, AttributeError):
            return None


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

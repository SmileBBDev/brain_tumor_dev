from django.db import models
from django.utils import timezone
from apps.patients.models import Patient
from apps.encounters.models import Encounter
from apps.accounts.models import User


class ImagingStudy(models.Model):
    """영상 검사 오더 및 메타데이터"""

    MODALITY_CHOICES = [
        ('CT', 'CT (Computed Tomography)'),
        ('MRI', 'MRI (Magnetic Resonance Imaging)'),
        ('PET', 'PET (Positron Emission Tomography)'),
        ('X-RAY', 'X-Ray'),
    ]

    STATUS_CHOICES = [
        ('ordered', '오더 생성'),
        ('scheduled', '검사 예약'),
        ('in-progress', '검사 수행 중'),
        ('completed', '검사 완료'),
        ('reported', '판독 완료'),
        ('cancelled', '취소'),
    ]

    # OCS 연동 - 재설계 후 추가 예정
    # order = models.ForeignKey(
    #     'ocs.OCSRequest',
    #     on_delete=models.PROTECT,
    #     null=True,
    #     blank=True,
    #     related_name='imaging_study',
    #     verbose_name='OCS 요청'
    # )

    # 기본 정보
    patient = models.ForeignKey(
        Patient,
        on_delete=models.PROTECT,
        related_name='imaging_studies',
        verbose_name='환자'
    )
    encounter = models.ForeignKey(
        Encounter,
        on_delete=models.PROTECT,
        related_name='imaging_studies',
        verbose_name='진료'
    )

    # 검사 정보
    modality = models.CharField(
        max_length=20,
        choices=MODALITY_CHOICES,
        verbose_name='검사 종류'
    )
    body_part = models.CharField(
        max_length=100,
        default='brain',
        verbose_name='촬영 부위'
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='ordered',
        verbose_name='검사 상태'
    )

    # 오더 정보
    ordered_by = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        related_name='ordered_imaging_studies',
        verbose_name='오더 의사'
    )
    ordered_at = models.DateTimeField(
        default=timezone.now,
        verbose_name='오더 일시'
    )

    # 검사 일정
    scheduled_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='예약 일시'
    )
    performed_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='검사 수행 일시'
    )

    # 판독 정보
    radiologist = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='read_imaging_studies',
        verbose_name='판독의'
    )

    # DICOM 메타데이터 (추후 Orthanc 연동용)
    study_uid = models.CharField(
        max_length=200,
        null=True,
        blank=True,
        unique=True,
        verbose_name='Study Instance UID'
    )
    series_count = models.IntegerField(
        default=0,
        verbose_name='시리즈 수'
    )
    instance_count = models.IntegerField(
        default=0,
        verbose_name='이미지 수'
    )

    # 기타
    clinical_info = models.TextField(
        blank=True,
        verbose_name='임상 정보'
    )
    special_instruction = models.TextField(
        blank=True,
        verbose_name='특별 지시사항'
    )

    # Soft Delete
    is_deleted = models.BooleanField(
        default=False,
        verbose_name='삭제 여부'
    )

    # 타임스탬프
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='생성 일시'
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name='수정 일시'
    )

    class Meta:
        db_table = 'imaging_studies'
        ordering = ['-ordered_at']
        indexes = [
            models.Index(fields=['patient', 'ordered_at']),
            models.Index(fields=['encounter']),
            models.Index(fields=['status']),
            models.Index(fields=['modality']),
        ]
        verbose_name = '영상 검사'
        verbose_name_plural = '영상 검사 목록'

    def __str__(self):
        return f"{self.get_modality_display()} - {self.patient.name} ({self.ordered_at.strftime('%Y-%m-%d')})"

    @property
    def is_completed(self):
        """검사 완료 여부"""
        return self.status in ['completed', 'reported']

    @property
    def has_report(self):
        """판독문 존재 여부"""
        return hasattr(self, 'report')


class ImagingReport(models.Model):
    """영상 검사 판독문"""

    STATUS_CHOICES = [
        ('draft', '작성 중'),
        ('signed', '서명 완료'),
        ('amended', '수정됨'),
    ]

    # 기본 정보
    imaging_study = models.OneToOneField(
        ImagingStudy,
        on_delete=models.CASCADE,
        related_name='report',
        verbose_name='영상 검사'
    )
    radiologist = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        related_name='imaging_reports',
        verbose_name='판독의'
    )

    # 판독 내용
    findings = models.TextField(
        verbose_name='판독 소견'
    )
    impression = models.TextField(
        verbose_name='판독 결론'
    )

    # 종양 정보
    tumor_detected = models.BooleanField(
        default=False,
        verbose_name='종양 발견 여부'
    )
    tumor_location = models.JSONField(
        null=True,
        blank=True,
        verbose_name='종양 위치'
    )
    tumor_size = models.JSONField(
        null=True,
        blank=True,
        verbose_name='종양 크기'
    )

    # 상태
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='draft',
        verbose_name='판독문 상태'
    )
    signed_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='서명 일시'
    )

    # 타임스탬프
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='생성 일시'
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name='수정 일시'
    )

    class Meta:
        db_table = 'imaging_reports'
        ordering = ['-created_at']
        verbose_name = '영상 판독문'
        verbose_name_plural = '영상 판독문 목록'

    def __str__(self):
        return f"판독문 - {self.imaging_study}"

    @property
    def is_signed(self):
        """서명 완료 여부"""
        return self.status == 'signed' and self.signed_at is not None

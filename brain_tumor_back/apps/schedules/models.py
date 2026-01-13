from django.db import models
from django.core.exceptions import ValidationError


class DoctorSchedule(models.Model):
    """
    의사 개인 일정 모델

    의사의 개인 일정(회의, 휴가, 교육 등)을 관리합니다.
    환자 진료 일정은 Encounter 모델에서 관리됩니다.
    """

    class ScheduleType(models.TextChoices):
        MEETING = 'meeting', '회의'
        LEAVE = 'leave', '휴가'
        TRAINING = 'training', '교육'
        PERSONAL = 'personal', '개인'
        OTHER = 'other', '기타'

    # 기본 색상 (일정 유형별)
    DEFAULT_COLORS = {
        'meeting': '#5b8def',    # 파랑
        'leave': '#e56b6f',      # 빨강
        'training': '#f2a65a',   # 주황
        'personal': '#5fb3a2',   # 초록
        'other': '#9ca3af',      # 회색
    }

    # 의사
    doctor = models.ForeignKey(
        'accounts.User',
        on_delete=models.CASCADE,
        related_name='schedules',
        verbose_name='의사'
    )

    # 일정 정보
    title = models.CharField(
        max_length=200,
        verbose_name='일정 제목'
    )

    schedule_type = models.CharField(
        max_length=20,
        choices=ScheduleType.choices,
        default=ScheduleType.OTHER,
        verbose_name='일정 유형'
    )

    description = models.TextField(
        blank=True,
        default='',
        verbose_name='설명'
    )

    # 일시
    start_datetime = models.DateTimeField(
        verbose_name='시작 일시'
    )

    end_datetime = models.DateTimeField(
        verbose_name='종료 일시'
    )

    all_day = models.BooleanField(
        default=False,
        verbose_name='종일 여부'
    )

    # 표시 색상 (선택)
    color = models.CharField(
        max_length=7,
        blank=True,
        default='',
        verbose_name='색상',
        help_text='HEX 코드 (예: #5b8def). 비워두면 일정 유형별 기본 색상 사용'
    )

    # 메타 정보
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='생성일시')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='수정일시')
    is_deleted = models.BooleanField(default=False, verbose_name='삭제 여부')

    class Meta:
        db_table = 'doctor_schedules'
        verbose_name = '의사 일정'
        verbose_name_plural = '의사 일정 목록'
        ordering = ['start_datetime']
        indexes = [
            models.Index(fields=['doctor', 'start_datetime']),
            models.Index(fields=['doctor', '-start_datetime']),
            models.Index(fields=['schedule_type']),
        ]

    def __str__(self):
        return f"[{self.get_schedule_type_display()}] {self.title} ({self.doctor.name})"

    def clean(self):
        """유효성 검사"""
        if self.start_datetime and self.end_datetime:
            if self.end_datetime <= self.start_datetime:
                raise ValidationError({
                    'end_datetime': '종료 일시는 시작 일시 이후여야 합니다.'
                })

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    @property
    def display_color(self):
        """표시할 색상 반환 (사용자 지정 또는 기본값)"""
        if self.color:
            return self.color
        return self.DEFAULT_COLORS.get(self.schedule_type, '#9ca3af')

    @property
    def duration_hours(self):
        """일정 시간 (시간 단위)"""
        if self.start_datetime and self.end_datetime:
            delta = self.end_datetime - self.start_datetime
            return round(delta.total_seconds() / 3600, 1)
        return 0

import uuid
from django.db import models
from django.conf import settings


class RadiologyOrder(models.Model):
    """영상 검사 오더"""
    STATUS_CHOICES = [
        ('ORDERED', 'Ordered'),
        ('SCHEDULED', 'Scheduled'),
        ('IN_PROGRESS', 'In Progress'),
        ('COMPLETED', 'Completed'),
        ('CANCELLED', 'Cancelled'),
    ]
    
    MODALITY_CHOICES = [
        ('CT', 'CT'),
        ('MRI', 'MRI'),
        ('XR', 'X-Ray'),
        ('US', 'Ultrasound'),
        ('NM', 'Nuclear Medicine'),
    ]
    
    order_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    patient_id = models.CharField(max_length=100, help_text="OpenEMR patient ID")
    ordered_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='radiology_orders')
    modality = models.CharField(max_length=10, choices=MODALITY_CHOICES)
    body_part = models.CharField(max_length=100)
    clinical_info = models.TextField(blank=True, help_text="임상 정보 및 검사 목적")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='ORDERED')
    priority = models.CharField(max_length=20, default='ROUTINE')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['patient_id', 'created_at']),
            models.Index(fields=['status']),
        ]
    
    def __str__(self):
        return f"{self.modality} - {self.patient_id} ({self.status})"


class RadiologyStudy(models.Model):
    """DICOM Study (Orthanc와 동기화)"""
    study_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    order = models.ForeignKey(RadiologyOrder, on_delete=models.SET_NULL, null=True, blank=True, related_name='studies')
    
    # Orthanc 정보
    orthanc_study_id = models.CharField(max_length=100, unique=True, help_text="Orthanc 내부 Study ID")
    study_instance_uid = models.CharField(max_length=255, unique=True, help_text="DICOM StudyInstanceUID")
    
    # DICOM 메타데이터
    patient_name = models.CharField(max_length=200)
    # DB에는 'patient_id' 컬럼만 있으므로 이를 ForeignKey로 사용
    patient = models.ForeignKey('emr.PatientCache', on_delete=models.SET_NULL, null=True, blank=True, related_name='radiology_studies', db_column='patient_id', help_text="매칭된 환자 정보")

    
    study_date = models.DateField(null=True, blank=True)
    study_time = models.TimeField(null=True, blank=True)
    study_description = models.TextField(blank=True)
    modality = models.CharField(max_length=10, blank=True)
    referring_physician = models.CharField(max_length=200, blank=True)
    
    # Study 통계
    num_series = models.IntegerField(default=0)
    num_instances = models.IntegerField(default=0)
    
    # 타임스탬프
    created_at = models.DateTimeField(auto_now_add=True)
    synced_at = models.DateTimeField(auto_now=True, help_text="Orthanc와 마지막 동기화 시간")
    
    class Meta:
        ordering = ['-study_date', '-study_time']
        indexes = [
            models.Index(fields=['patient', 'study_date']),
            models.Index(fields=['orthanc_study_id']),
        ]

    def __str__(self):
        return f"{self.patient_name} - {self.study_date} ({self.modality})"

    @property
    def dicom_web_url(self):
        """
        DICOM-Web URL (JWT 토큰 포함, 1시간 유효)
        캐시된 URL이 있으면 반환, 없으면 Orthanc에서 새로 생성
        """
        try:
            from .clients.orthanc_client import OrthancClient
            client = OrthancClient()
            # Orthanc ID와 StudyUID를 모두 전달
            jwt_url_data = client.get_study_url_with_jwt(self.orthanc_study_id, self.study_instance_uid)

            if jwt_url_data.get('token'):
                return f"{jwt_url_data['url']}?token={jwt_url_data['token']}"
            return jwt_url_data['url']
        except Exception as e:
            # 절대 에러를 발생시키지 않음 (기본 URL 반환)
            from django.conf import settings
            return f"{settings.ORTHANC_API_URL}/dicom-web/studies/{self.study_instance_uid}"

    @property
    def jwt_token_expires_at(self):
        """JWT 토큰 만료 시각"""
        from django.core.cache import cache

        cache_key = f"orthanc_jwt_url:study:{self.study_instance_uid}"
        cached_url = cache.get(cache_key)

        if cached_url:
            from datetime import datetime
            return datetime.fromisoformat(cached_url['expires_at'])

        return None


class RadiologyReport(models.Model):
    """영상 판독문"""
    STATUS_CHOICES = [
        ('DRAFT', 'Draft'),
        ('PRELIMINARY', 'Preliminary'),
        ('FINAL', 'Final'),
        ('AMENDED', 'Amended'),
    ]
    
    report_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    study = models.OneToOneField(RadiologyStudy, on_delete=models.CASCADE, related_name='report')
    radiologist = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='radiology_reports')
    
    findings = models.TextField(help_text="판독 소견")
    impression = models.TextField(help_text="판독 결론")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='DRAFT')
    
    # 서명
    signed_at = models.DateTimeField(null=True, blank=True)
    signed_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='signed_reports')
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Report for {self.study.patient_name} - {self.status}"

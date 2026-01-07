"""
Patient (환자) 앱 모델

환자 본인의 정보 조회 기능
- 본인 진료 기록 조회
- 처방 내역 조회
- 검사 결과 조회
"""

from django.db import models

# 공통 모델 사용 (읽기 전용)
from apps.common.models import Patient, Encounter, Order

__all__ = ['Patient', 'Encounter', 'Order']

# TODO: 향후 추가할 모델
# class PatientAppointment(models.Model):
#     """환자 예약 정보"""
#     pass

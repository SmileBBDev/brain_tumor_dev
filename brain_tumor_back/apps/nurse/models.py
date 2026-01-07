"""
Nurse (간호사) 앱 모델

간호사의 업무를 담당
- 환자 등록 및 정보 수정
- 바이탈 사인 입력
- 처방 실행 확인
"""

from django.db import models

# 공통 모델 사용
from apps.common.models import Patient, Order

__all__ = ['Patient', 'Order']

# TODO: 향후 추가할 모델
# class PatientVitals(models.Model):
#     """바이탈 사인 (혈압, 맥박, 체온 등)"""
#     pass
#
# class MedicationAdministration(models.Model):
#     """약물 투여 기록"""
#     pass

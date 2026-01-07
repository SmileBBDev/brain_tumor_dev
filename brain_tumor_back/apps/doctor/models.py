"""
Doctor (의사) 앱 모델

의사의 진료 업무를 담당
- 환자 조회 및 진료 기록 작성
- 처방 발행
- 진단 코드 입력
"""

from django.db import models

# 공통 모델 사용
from apps.common.models import (
    Patient,
    Encounter,
    EncounterDiagnosis,
    Order,
    OrderItem
)

# 마스터 데이터 참조
from apps.ocs.models import MedicationMaster, DiagnosisMaster

__all__ = [
    'Patient', 'Encounter', 'EncounterDiagnosis',
    'Order', 'OrderItem',
    'MedicationMaster', 'DiagnosisMaster'
]

"""
Admin Clinical (관리자) 앱 모델

마스터 데이터 관리를 담당
- 약물 마스터 데이터
- 진단 마스터 데이터
- 검사 마스터 데이터
"""

from django.db import models

# 기존 ocs 모델 import (하위 호환성)
from apps.ocs.models import MedicationMaster, DiagnosisMaster

# lis 모델도 참조 (검사 마스터 관리)
from apps.lis.models import LabTestMaster

__all__ = ['MedicationMaster', 'DiagnosisMaster', 'LabTestMaster']

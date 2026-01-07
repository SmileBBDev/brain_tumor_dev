"""
Lab Technician (검사실 기사) 앱 모델

LIS (Laboratory Information System) 기능을 담당
- 검사 마스터 데이터
- 검사 결과 입력 및 관리
"""

from django.db import models
from apps.common.models import Patient, Order

# 기존 lis 모델 import (하위 호환성)
from apps.lis.models import LabTestMaster, LabResult

__all__ = ['LabTestMaster', 'LabResult']

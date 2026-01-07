"""
Radiologist (영상의학과 의사) 앱 모델

RIS (Radiology Information System) 기능을 담당
- 영상 검사 오더
- DICOM 영상 Study
- 판독 Report
"""

import uuid
from django.db import models
from django.conf import settings
from apps.common.models import Patient

# 기존 ris 모델 import (하위 호환성)
from apps.ris.models import RadiologyOrder, RadiologyStudy, RadiologyReport

__all__ = ['RadiologyOrder', 'RadiologyStudy', 'RadiologyReport']

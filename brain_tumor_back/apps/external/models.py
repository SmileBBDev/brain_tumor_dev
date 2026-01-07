"""
External (외부 기관 연동) 앱 모델

외부 시스템 연동 기능을 담당
- FHIR 리소스 매핑
- FHIR 동기화 큐
- Sync Outbox (OpenEMR 등)
"""

from django.db import models

# 기존 fhir 모델 import (하위 호환성)
from apps.fhir.models import FHIRResourceMap, FHIRSyncQueue

# emr의 SyncOutbox 모델 import
from apps.emr.models import SyncOutbox

__all__ = ['FHIRResourceMap', 'FHIRSyncQueue', 'SyncOutbox']

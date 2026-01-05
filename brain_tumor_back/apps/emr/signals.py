"""
EMR Auto-Sync Signals (DEPRECATED)

⚠️ DEPRECATED: Signal 기반 동기화는 더 이상 사용되지 않습니다.

새로운 아키텍처:
- Outbox 패턴 + Celery 비동기 동기화
- Service 레이어에서 Outbox 레코드 생성
- Celery Worker가 백그라운드에서 동기화 처리
- 재시도 로직(Exponential Backoff)으로 데이터 유실 방지

이전 방식 (Signal):
- PatientCache 생성/수정 → OpenEMR Patient + FHIR Patient
- Encounter 생성/수정 → OpenEMR Encounter (TODO)
- Order 생성/수정 → OpenEMR MedicationRequest (TODO)
"""

from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.conf import settings
import logging

from .models import PatientCache, Encounter, Order
from .services.openemr_client import OpenEMRClient
from .services.openemr_mapper import (
    patient_cache_to_openemr_patient,
    openemr_patient_to_dict,
)

logger = logging.getLogger(__name__)


# OpenEMR Client 초기화
def get_openemr_client():
    """OpenEMR Client 싱글톤"""
    if not hasattr(get_openemr_client, '_client'):
        get_openemr_client._client = OpenEMRClient()
    return get_openemr_client._client


# ============================================
# PatientCache → OpenEMR 자동 동기화
# ============================================

# Signal을 비활성화 - Outbox 패턴 사용
# @receiver(post_save, sender=PatientCache)
def sync_patient_to_openemr_DEPRECATED(sender, instance, created, **kwargs):
    """
    환자 생성/수정 시 OpenEMR Patient 리소스로 동기화

    Args:
        instance: PatientCache 모델 인스턴스
        created: 신규 생성 여부
    """
    try:
        openemr_client = get_openemr_client()
        openemr_patient = patient_cache_to_openemr_patient(instance)

        if created or not instance.openemr_patient_id:
            # 신규 환자 → OpenEMR 생성
            result = openemr_client.create_patient(openemr_patient)
            if result and 'id' in result:
                instance.openemr_patient_id = result['id']
                instance.last_synced_at = instance.updated_at
                instance.save(update_fields=['openemr_patient_id', 'last_synced_at'])
                logger.info(f'✓ OpenEMR Patient created: {instance.patient_id} → {result["id"]}')
        else:
            # 기존 환자 → OpenEMR 업데이트
            result = openemr_client.update_patient(instance.openemr_patient_id, openemr_patient)
            if result:
                instance.last_synced_at = instance.updated_at
                instance.save(update_fields=['last_synced_at'])
                logger.info(f'✓ OpenEMR Patient updated: {instance.patient_id} → {instance.openemr_patient_id}')

    except Exception as e:
        logger.error(f'✗ OpenEMR sync failed for Patient {instance.patient_id}: {str(e)}')


# @receiver(post_delete, sender=PatientCache)
def delete_patient_from_openemr_DEPRECATED(sender, instance, **kwargs):
    """환자 삭제 시 OpenEMR에서도 삭제"""
    if instance.openemr_patient_id:
        try:
            openemr_client = get_openemr_client()
            openemr_client.delete_patient(instance.openemr_patient_id)
            logger.info(f'✓ OpenEMR Patient deleted: {instance.openemr_patient_id}')
        except Exception as e:
            logger.error(f'✗ OpenEMR delete failed for Patient {instance.openemr_patient_id}: {str(e)}')


# ============================================
# Encounter → OpenEMR 자동 동기화 (TODO)
# ============================================

# @receiver(post_save, sender=Encounter)
def sync_encounter_to_openemr(sender, instance, created, **kwargs):
    """
    진료 생성/수정 시 OpenEMR Encounter 리소스로 동기화

    TODO: Encounter에 openemr_encounter_id 필드 추가 후 활성화
    """
    pass


# ============================================
# Order → OpenEMR 자동 동기화 (TODO)
# ============================================

# @receiver(post_save, sender=Order)
def sync_order_to_openemr(sender, instance, created, **kwargs):
    """
    처방 생성/수정 시 OpenEMR MedicationRequest 리소스로 동기화

    TODO: Order에 openemr_order_id 필드 추가 후 활성화
    """
    pass

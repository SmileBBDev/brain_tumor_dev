"""
EMR Celery Tasks

Outbox 패턴을 활용한 비동기 동기화 작업
- OpenEMR 동기화
- FHIR 서버 동기화
- 재시도 로직 (Exponential Backoff)
"""

from celery import shared_task
from django.utils import timezone
from django.db import transaction
import logging

from .models import SyncOutbox, PatientCache
from .services.openemr_client import OpenEMRClient
from .services.openemr_mapper import patient_cache_to_openemr_patient
from .repositories import OpenEMRPatientRepository

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=5, default_retry_delay=60)
def process_sync_outbox(self, outbox_id: str):
    """
    Outbox 레코드 처리

    Args:
        outbox_id: SyncOutbox의 UUID

    Returns:
        dict: 처리 결과
    """
    try:
        # Outbox 레코드 조회
        outbox = SyncOutbox.objects.get(outbox_id=outbox_id)

        # 이미 처리 완료된 경우 스킵
        if outbox.status == 'done':
            logger.info(f"Outbox {outbox_id} already processed, skipping")
            return {'status': 'skipped', 'reason': 'already_done'}

        # 처리 중으로 상태 변경
        outbox.mark_as_processing()

        # 타겟 시스템에 따라 분기
        if outbox.target_system == 'openemr':
            result = _sync_to_openemr(outbox)
        elif outbox.target_system == 'fhir':
            result = _sync_to_fhir(outbox)
        else:
            raise ValueError(f"Unknown target system: {outbox.target_system}")

        if result['success']:
            # 성공 - 완료 처리
            outbox.mark_as_done()
            logger.info(f"✓ Outbox {outbox_id} processed successfully")
            return {'status': 'success', 'outbox_id': str(outbox_id)}
        else:
            # 실패 - 재시도 예약
            error_msg = result.get('error', 'Unknown error')
            outbox.mark_as_failed(error_msg)
            logger.warning(f"✗ Outbox {outbox_id} failed: {error_msg}")

            # Celery 태스크 재시도 예약
            if outbox.is_retryable and outbox.next_retry_at:
                eta = outbox.next_retry_at
                logger.info(f"Scheduling retry for {outbox_id} at {eta}")
                raise self.retry(exc=Exception(error_msg), eta=eta)
            else:
                logger.error(f"Max retries exceeded for {outbox_id}")
                return {'status': 'failed', 'outbox_id': str(outbox_id), 'error': error_msg}

    except SyncOutbox.DoesNotExist:
        logger.error(f"Outbox {outbox_id} not found")
        return {'status': 'error', 'reason': 'not_found'}

    except Exception as e:
        logger.exception(f"Unexpected error processing outbox {outbox_id}: {str(e)}")
        return {'status': 'error', 'error': str(e)}


def _sync_to_openemr(outbox: SyncOutbox) -> dict:
    """
    OpenEMR로 동기화

    Args:
        outbox: SyncOutbox 레코드

    Returns:
        dict: {'success': bool, 'error': str}
    """
    try:
        # openemr_client = OpenEMRClient() # Deprecated: Direct DB Access 사용

        if outbox.entity_type == 'patient':
            # Patient 동기화
            patient = PatientCache.objects.get(patient_id=outbox.entity_id)
            # openemr_patient = patient_cache_to_openemr_patient(patient) # DB 직접 접근시에는 data dict 필요

            if outbox.operation == 'create':
                # create_patient_in_openemr expects a dict similar to PatientCache
                # outbox.payload might contain the data, or we use the patient instance
                # For consistency with repository, we reconstruct data from patient instance
                data = {
                    'patient_id': patient.patient_id,
                    'given_name': patient.given_name,
                    'family_name': patient.family_name,
                    'birth_date': patient.birth_date,
                    'gender': patient.gender,
                    'phone': patient.phone,
                    'email': patient.email,
                    'address': patient.address,
                }
                new_pid = OpenEMRPatientRepository.create_patient_in_openemr(data)
                
                if new_pid:
                    # OpenEMR Patient ID 저장
                    patient.openemr_patient_id = str(new_pid)
                    patient.last_synced_at = timezone.now()
                    patient.save(update_fields=['openemr_patient_id', 'last_synced_at'])
                    return {'success': True}
                else:
                    return {'success': False, 'error': 'Failed to create patient in OpenEMR DB'}

            elif outbox.operation == 'update':
                if not patient.openemr_patient_id:
                     # ID가 없으면 Create로 Fallback하거나 에러
                    return {'success': False, 'error': 'No OpenEMR patient ID to update'}

                data = {
                    'given_name': patient.given_name,
                    'family_name': patient.family_name,
                    'birth_date': patient.birth_date,
                    'gender': patient.gender,
                    'phone': patient.phone,
                    'email': patient.email,
                    'address': patient.address,
                }
                # pid는 int여야 함
                pid = int(patient.openemr_patient_id)
                success = OpenEMRPatientRepository.update_patient_in_openemr(pid, data)
                
                if success:
                    patient.last_synced_at = timezone.now()
                    patient.save(update_fields=['last_synced_at'])
                    return {'success': True}
                else:
                    return {'success': False, 'error': 'OpenEMR update failed'}

            elif outbox.operation == 'delete':
                if patient.openemr_patient_id:
                    pid = int(patient.openemr_patient_id)
                    success = OpenEMRPatientRepository.delete_patient_in_openemr(pid)
                    return {'success': success}
                return {'success': True}  # Already deleted

        elif outbox.entity_type == 'encounter':
            # TODO: Encounter 동기화 구현
            return {'success': True}

        elif outbox.entity_type == 'order':
            # TODO: Order 동기화 구현
            return {'success': True}

        return {'success': False, 'error': f'Unknown entity type: {outbox.entity_type}'}

    except PatientCache.DoesNotExist:
        return {'success': False, 'error': f'Patient {outbox.entity_id} not found'}

    except Exception as e:
        return {'success': False, 'error': str(e)}


def _sync_to_fhir(outbox: SyncOutbox) -> dict:
    """
    FHIR 서버로 동기화 (User Requirement: Use Direct DB Access mostly)
    
    사용자의 요구에 따라 FHIR 타겟도 OpenEMR DB 직접 접근 방식을 사용하여 동기화합니다.
    (실제 FHIR 표준 API를 사용해야 하는 경우 이 부분을 원복하거나 openemr_client를 사용해야 함)
    """
    # Simply delegate to _sync_to_openemr for now, assuming same DB target
    return _sync_to_openemr(outbox)


@shared_task
def retry_failed_outbox():
    """
    실패한 Outbox 재시도

    Celery Beat에서 주기적으로 실행 (예: 매 1분)
    - status='failed'이고 next_retry_at이 현재 시간 이전인 레코드 재처리
    """
    now = timezone.now()

    # 재시도 대상 조회
    failed_outboxes = SyncOutbox.objects.filter(
        status='failed',
        next_retry_at__lte=now
    ).order_by('next_retry_at')[:100]  # 한 번에 최대 100개

    logger.info(f"Found {failed_outboxes.count()} failed outbox records to retry")

    for outbox in failed_outboxes:
        logger.info(f"Retrying outbox {outbox.outbox_id} (attempt {outbox.retry_count + 1})")
        process_sync_outbox.delay(str(outbox.outbox_id))

    return {
        'status': 'success',
        'retried_count': failed_outboxes.count(),
        'timestamp': now.isoformat()
    }


@shared_task
def cleanup_old_outbox():
    """
    오래된 Outbox 레코드 정리

    Celery Beat에서 주기적으로 실행 (예: 매일 새벽 3시)
    - status='done'이고 7일 이상 지난 레코드 삭제
    """
    from datetime import timedelta
    cutoff_date = timezone.now() - timedelta(days=7)

    deleted_count, _ = SyncOutbox.objects.filter(
        status='done',
        processed_at__lt=cutoff_date
    ).delete()

    logger.info(f"Cleaned up {deleted_count} old outbox records")

    return {
        'status': 'success',
        'deleted_count': deleted_count,
        'cutoff_date': cutoff_date.isoformat()
    }

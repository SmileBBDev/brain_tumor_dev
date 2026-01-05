"""
FHIR Auto-Sync Signals

Django 모델이 생성/수정될 때 자동으로 FHIR 서버에 동기화합니다.

Signals:
- Patient 생성/수정 → FHIR Patient Resource
- Prescription 생성/수정 → FHIR MedicationRequest Resource
- LabTest 생성/수정 → FHIR DiagnosticReport + Observation Resources
"""

from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.conf import settings
import logging

from emr.models import PatientCache
# TODO: Prescription, LabTest 모델 생성 후 활성화
# from ocs.models import Prescription
# from lis.models import LabTest, LabResult
from .services.fhir_client import FHIRClient
from .services.fhir_mapper import (
    patient_to_fhir,
    prescription_to_fhir,
    lab_test_to_fhir,
)

logger = logging.getLogger(__name__)


# FHIR Client 초기화
def get_fhir_client():
    """FHIR Client 싱글톤"""
    if not hasattr(get_fhir_client, '_client'):
        fhir_url = getattr(settings, 'FHIR_SERVER_URL', 'http://localhost:8080/fhir')
        get_fhir_client._client = FHIRClient(fhir_url)
    return get_fhir_client._client


# ============================================
# Patient 자동 동기화
# ============================================

@receiver(post_save, sender=PatientCache)
def sync_patient_to_fhir(sender, instance, created, **kwargs):
    """
    환자 생성/수정 시 FHIR Patient 리소스로 동기화

    Args:
        instance: Patient 모델 인스턴스
        created: 신규 생성 여부
    """
    try:
        fhir_client = get_fhir_client()
        fhir_patient = patient_to_fhir(instance)

        if created or not instance.fhir_id:
            # 신규 환자 → FHIR 생성
            result = fhir_client.create_resource('Patient', fhir_patient)
            if result and 'id' in result:
                instance.fhir_id = result['id']
                instance.save(update_fields=['fhir_id'])
                logger.info(f'✓ FHIR Patient created: {instance.patient_id} → {result["id"]}')
        else:
            # 기존 환자 → FHIR 업데이트
            result = fhir_client.update_resource('Patient', instance.fhir_id, fhir_patient)
            if result:
                logger.info(f'✓ FHIR Patient updated: {instance.patient_id} → {instance.fhir_id}')

    except Exception as e:
        logger.error(f'✗ FHIR sync failed for Patient {instance.patient_id}: {str(e)}')


@receiver(post_delete, sender=PatientCache)
def delete_patient_from_fhir(sender, instance, **kwargs):
    """환자 삭제 시 FHIR에서도 삭제"""
    if instance.fhir_id:
        try:
            fhir_client = get_fhir_client()
            fhir_client.delete_resource('Patient', instance.fhir_id)
            logger.info(f'✓ FHIR Patient deleted: {instance.fhir_id}')
        except Exception as e:
            logger.error(f'✗ FHIR delete failed for Patient {instance.fhir_id}: {str(e)}')


# ============================================
# Prescription 자동 동기화 (TODO: Prescription 모델 생성 후 활성화)
# ============================================

# @receiver(post_save, sender=Prescription)
def sync_prescription_to_fhir(sender, instance, created, **kwargs):
    """
    처방 생성/수정 시 FHIR MedicationRequest 리소스로 동기화
    """
    try:
        # 환자의 FHIR ID가 있어야 함
        if not instance.patient.fhir_id:
            logger.warning(f'Patient {instance.patient.patient_id} has no FHIR ID, syncing patient first')
            sync_patient_to_fhir(PatientCache, instance.patient, False)

        fhir_client = get_fhir_client()
        fhir_medication_request = prescription_to_fhir(instance)

        if created or not instance.fhir_id:
            # 신규 처방 → FHIR 생성
            result = fhir_client.create_resource('MedicationRequest', fhir_medication_request)
            if result and 'id' in result:
                instance.fhir_id = result['id']
                instance.save(update_fields=['fhir_id'])
                logger.info(f'✓ FHIR MedicationRequest created: Prescription #{instance.id} → {result["id"]}')
        else:
            # 기존 처방 → FHIR 업데이트
            result = fhir_client.update_resource('MedicationRequest', instance.fhir_id, fhir_medication_request)
            if result:
                logger.info(f'✓ FHIR MedicationRequest updated: Prescription #{instance.id} → {instance.fhir_id}')

    except Exception as e:
        logger.error(f'✗ FHIR sync failed for Prescription #{instance.id}: {str(e)}')


# ============================================
# LabTest 자동 동기화 (TODO: LabTest 모델 생성 후 활성화)
# ============================================

# @receiver(post_save, sender=LabTest)
def sync_lab_test_to_fhir(sender, instance, created, **kwargs):
    """
    검사 생성/수정 시 FHIR DiagnosticReport + Observation 리소스로 동기화
    """
    try:
        # 환자의 FHIR ID가 있어야 함
        if not instance.patient.fhir_id:
            logger.warning(f'Patient {instance.patient.patient_id} has no FHIR ID, syncing patient first')
            sync_patient_to_fhir(PatientCache, instance.patient, False)

        fhir_client = get_fhir_client()
        fhir_diagnostic_report = lab_test_to_fhir(instance)

        if created or not instance.fhir_id:
            # 신규 검사 → FHIR 생성
            result = fhir_client.create_resource('DiagnosticReport', fhir_diagnostic_report)
            if result and 'id' in result:
                instance.fhir_id = result['id']
                instance.save(update_fields=['fhir_id'])
                logger.info(f'✓ FHIR DiagnosticReport created: LabTest #{instance.id} → {result["id"]}')

                # 검사 결과(Observation) 동기화
                sync_lab_results_to_fhir(instance)
        else:
            # 기존 검사 → FHIR 업데이트
            result = fhir_client.update_resource('DiagnosticReport', instance.fhir_id, fhir_diagnostic_report)
            if result:
                logger.info(f'✓ FHIR DiagnosticReport updated: LabTest #{instance.id} → {instance.fhir_id}')
                sync_lab_results_to_fhir(instance)

    except Exception as e:
        logger.error(f'✗ FHIR sync failed for LabTest #{instance.id}: {str(e)}')


def sync_lab_results_to_fhir(lab_test):
    """검사 결과를 FHIR Observation으로 동기화"""
    from .services.fhir_mapper import lab_result_to_fhir

    fhir_client = get_fhir_client()

    for lab_result in lab_test.results.all():
        try:
            fhir_observation = lab_result_to_fhir(lab_result, lab_test)

            if not lab_result.fhir_id:
                result = fhir_client.create_resource('Observation', fhir_observation)
                if result and 'id' in result:
                    lab_result.fhir_id = result['id']
                    lab_result.save(update_fields=['fhir_id'])
                    logger.info(f'  ✓ FHIR Observation created: {lab_result.test_name} → {result["id"]}')
            else:
                result = fhir_client.update_resource('Observation', lab_result.fhir_id, fhir_observation)
                if result:
                    logger.info(f'  ✓ FHIR Observation updated: {lab_result.test_name} → {lab_result.fhir_id}')
        except Exception as e:
            logger.error(f'  ✗ FHIR sync failed for LabResult #{lab_result.id}: {str(e)}')


# ============================================
# Management Command: Bulk Sync
# ============================================

def bulk_sync_to_fhir(model_name=None):
    """
    기존 데이터를 일괄 FHIR 동기화

    Usage:
        from fhir.signals import bulk_sync_to_fhir
        bulk_sync_to_fhir('Patient')  # 모든 환자 동기화
        bulk_sync_to_fhir()  # 모든 데이터 동기화
    """
    models_to_sync = []

    if model_name == 'Patient' or not model_name:
        models_to_sync.append((PatientCache, sync_patient_to_fhir))

    # TODO: Prescription, LabTest 모델 생성 후 활성화
    # if model_name == 'Prescription' or not model_name:
    #     models_to_sync.append((Prescription, sync_prescription_to_fhir))
    #
    # if model_name == 'LabTest' or not model_name:
    #     models_to_sync.append((LabTest, sync_lab_test_to_fhir))

    for model, sync_func in models_to_sync:
        logger.info(f'Syncing {model.__name__}...')
        for instance in model.objects.all():
            sync_func(model, instance, created=False)

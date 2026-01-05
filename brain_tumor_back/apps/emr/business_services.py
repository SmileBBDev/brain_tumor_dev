
from datetime import datetime
from django.db import transaction
from django.utils import timezone
from .repositories import (
    PatientRepository,
    EncounterRepository,
    OrderRepository,
    OpenEMRPatientRepository,
    OpenEMROrderRepository
)
from .models import SyncOutbox
from .services.openemr_mapper import patient_cache_to_openemr_patient
import logging

logger = logging.getLogger(__name__)


class PatientService:
    """환자 비즈니스 로직"""

    @staticmethod
    def create_patient(data):
        """
        환자 생성 (Outbox Pattern with Celery)

        1. Atomic Transaction:
           - Django MySQL에 환자 정보 저장
           - 동기화 작업을 Outbox 테이블에 저장 (Pending)
        2. 빠른 응답 반환
        3. Celery Worker가 비동기로 OpenEMR 동기화 처리
        """
        year = datetime.now().year
        last_number = PatientRepository.get_max_patient_sequence(year)
        new_number = last_number + 1

        patient_id = f'P-{year}-{new_number:06d}'
        data['patient_id'] = patient_id

        persistence_status = {
            "django_emr_patient_cache": "대기",
            "openemr_sync_outbox": "대기"
        }

        try:
            with transaction.atomic():
                # 1. Django MySQL에 환자 정보 저장
                patient = PatientRepository.create_patient(data)
                persistence_status["django_emr_patient_cache"] = "성공"

                # 2. OpenEMR 동기화 작업을 Outbox에 저장
                openemr_patient_payload = patient_cache_to_openemr_patient(patient)

                outbox = SyncOutbox.objects.create(
                    entity_type='patient',
                    entity_id=patient_id,
                    operation='create',
                    target_system='openemr',
                    payload=openemr_patient_payload,
                    status='pending'
                )
                persistence_status["openemr_sync_outbox"] = f"대기중 ({outbox.outbox_id})"

                # 3. Celery Task 비동기 실행 (트랜잭션 커밋 후 실행)
                from .tasks import process_sync_outbox
                transaction.on_commit(lambda: process_sync_outbox.delay(str(outbox.outbox_id)))

                logger.info(f"✓ Patient {patient_id} created with outbox {outbox.outbox_id}")

            # [UC09] 감사 로그 (Transaction 바깥에서 실행 - 로그 저장이 실패해도 환자 생성은 유지)
            try:
                from audit.services import AuditService
                AuditService.log_action(
                    user=None,
                    action='CREATE',
                    app_label='emr',
                    model_name='PatientCache',
                    object_id=patient_id,
                    change_summary=f"환자 생성: {patient_id}"
                )
            except Exception as log_e:
                logger.warning(f"감사 로그 기록 실패 (환자 생성은 성공): {str(log_e)}")

            return patient, persistence_status

        except Exception as e:
            logger.error(f"Failed to create patient: {str(e)}")
            persistence_status["django_emr_patient_cache"] = f"실패: {str(e)}"
            raise e

    @staticmethod
    def update_patient(patient_id, data, use_pessimistic=True):
        """
        환자 정보 업데이트 (Outbox Pattern with Celery)

        1. Atomic Transaction:
           - Django MySQL에 환자 정보 업데이트
           - 동기화 작업을 Outbox 테이블에 저장 (Pending)
        2. 빠른 응답 반환
        3. Celery Worker가 비동기로 OpenEMR 동기화 처리
        """
        old_version = data.pop('version', None)

        try:
            with transaction.atomic():
                # 1. 비관적 락 (Pessimistic Locking)
                if use_pessimistic:
                    patient = PatientRepository.get_patient_by_id(patient_id, for_update=True)
                    if not patient:
                        raise Exception("환자를 찾을 수 없습니다.")

                # 2. 낙관적 락 (Optimistic Locking)
                if old_version is not None:
                    success = PatientRepository.update_patient_optimistic(patient_id, old_version, data)
                    if not success:
                        raise Exception("데이터 충돌이 발생했습니다. (Optimistic Lock Failure)")
                else:
                    # version이 없으면 일반 업데이트
                    PatientRepository.update_patient(patient_id, data)

                # 3. 업데이트된 환자 정보 조회
                updated_patient = PatientRepository.get_patient_by_id(patient_id)

                # 4. OpenEMR 동기화 작업을 Outbox에 저장
                openemr_patient_payload = patient_cache_to_openemr_patient(updated_patient)

                outbox = SyncOutbox.objects.create(
                    entity_type='patient',
                    entity_id=patient_id,
                    operation='update',
                    target_system='openemr',
                    payload=openemr_patient_payload,
                    status='pending'
                )

                # [UC09] 감사 로그
                from audit.services import AuditService
                AuditService.log_action(
                    user=None,
                    action='UPDATE',
                    app_label='emr',
                    model_name='PatientCache',
                    object_id=patient_id,
                    change_summary=f"환자 정보 수정: {patient_id}",
                    current_data=data
                )

                # 5. Celery Task 비동기 실행 (트랜잭션 커밋 후 실행)
                from .tasks import process_sync_outbox
                transaction.on_commit(lambda: process_sync_outbox.delay(str(outbox.outbox_id)))

                logger.info(f"✓ Patient {patient_id} updated with outbox {outbox.outbox_id}")

                return updated_patient

        except Exception as e:
            logger.error(f"Update failed for patient {patient_id}: {str(e)}")
            raise e


class EncounterService:
    """진료 기록 비즈니스 로직"""

    @staticmethod
    def create_encounter(data):
        """
        진료 기록 생성 (Parallel Dual-Write)
        - Django DB와 OpenEMR DB에 병렬적으로(독립적으로) 데이터 전달
        """
        from ocs.models import DiagnosisMaster
        from .models import EncounterDiagnosis
        from .repositories import OpenEMREncounterRepository

        year = datetime.now().year
        last_number = EncounterRepository.get_max_encounter_sequence(year)
        new_number = last_number + 1

        encounter_id = f'E-{year}-{new_number:06d}'
        data['encounter_id'] = encounter_id

        # 진단 데이터 추출
        diagnosis_items = data.pop('diagnoses', [])

        persistence_status = {
            "django_emr_encounters,django_emr_encounter_diagnoses": "대기",
            "openemr_sync_outbox": "대기"
        }

        encounter = None
        try:
            with transaction.atomic():
                # 1. Django DB 저장
                encounter = EncounterRepository.create_encounter(data)
                for idx, diag_item in enumerate(diagnosis_items, 1):
                    diag_code = diag_item.get('diag_code')
                    comments = diag_item.get('comments', '')
                    if diag_code:
                        try:
                            master = DiagnosisMaster.objects.get(diag_code=diag_code)
                            EncounterDiagnosis.objects.create(
                                encounter=encounter,
                                diag_code=diag_code,
                                diagnosis_name=master.name_ko,
                                priority=idx,
                                comments=comments
                            )
                        except DiagnosisMaster.DoesNotExist:
                            EncounterDiagnosis.objects.create(
                                encounter=encounter,
                                diag_code=diag_code,
                                diagnosis_name="Unknown Diagnosis",
                                priority=idx,
                                comments=comments
                            )
                persistence_status["django_emr_encounters,django_emr_encounter_diagnoses"] = "성공"

                # 2. Outbox 저장
                # Reconstruct payload for OpenEMR
                payload = data.copy()
                payload['patient_id'] = data.get('patient_id', '') # Ensure ID is present
                # Note: diagnosis items are separate in payload usually
                payload['diagnoses'] = diagnosis_items
                
                outbox = SyncOutbox.objects.create(
                    entity_type='encounter',
                    entity_id=encounter_id,
                    operation='create',
                    target_system='openemr',
                    payload=payload,
                    status='pending'
                )
                persistence_status["openemr_sync_outbox"] = f"대기중 ({outbox.outbox_id})"

                # 3. Async Task Trigger
                from .tasks import process_sync_outbox
                transaction.on_commit(lambda: process_sync_outbox.delay(str(outbox.outbox_id)))

        except Exception as e:
            logger.error(f"Failed to create encounter: {str(e)}")
            persistence_status["django_emr_encounters,django_emr_encounter_diagnoses"] = f"실패: {str(e)}"
            raise e

        return encounter, persistence_status


class OrderService:
    """처방 비즈니스 로직"""

    @staticmethod
    def create_order(order_data, items_data):
        """
        처방 생성 (Parallel Dual-Write)
        - Django DB와 OpenEMR DB에 독립적으로 요청 전달
        """
        from ocs.models import MedicationMaster

        year = datetime.now().year
        last_number = OrderRepository.get_max_order_sequence(year)
        new_number = last_number + 1

        order_id = f'O-{year}-{new_number:06d}'
        order_data['order_id'] = order_id

        # 항목 ID 생성 및 유효성 검사
        final_items_data = []
        order_type = order_data.get('order_type')
        
        for idx, item in enumerate(items_data, 1):
            code = item.get('drug_code') or item.get('test_code')
            if code:
                if order_type == 'medication':
                    try:
                        master = MedicationMaster.objects.get(drug_code=code)
                        item['drug_name'] = master.drug_name
                        item['drug_code'] = code # drug_code로 통일
                    except MedicationMaster.DoesNotExist:
                        raise Exception(f"유효하지 않은 약물 코드입니다: {code}")
                elif order_type == 'lab':
                    from lis.models import LabTestMaster
                    try:
                        master = LabTestMaster.objects.get(test_code=code)
                        item['drug_name'] = master.test_name # drug_name 필드를 test_name 용도로 공유 (OrderItem 모델 구조상)
                        item['drug_code'] = code
                    except LabTestMaster.DoesNotExist:
                        raise Exception(f"유효하지 않은 검사 코드입니다: {code}")

            item_id = f'OI-{order_id}-{idx:03d}'
            item['item_id'] = item_id
            final_items_data.append(item)

        persistence_status = {
            "django_emr_orders,django_emr_order_items": "대기",
            "openemr_sync_outbox": "대기"
        }

        order = None
        try:
            with transaction.atomic():
                # 1. Django DB 저장
                order = OrderRepository.create_order(order_data, final_items_data)
                persistence_status["django_emr_orders,django_emr_order_items"] = "성공"

                # 2. Outbox 저장
                # Payload Serialization: Convert Model objects to IDs
                payload_order_data = order_data.copy()
                if 'patient' in payload_order_data and hasattr(payload_order_data['patient'], 'patient_id'):
                    payload_order_data['patient'] = payload_order_data['patient'].patient_id
                if 'encounter' in payload_order_data and hasattr(payload_order_data['encounter'], 'encounter_id'):
                    payload_order_data['encounter'] = payload_order_data['encounter'].encounter_id
                if 'ordered_by' in payload_order_data and hasattr(payload_order_data['ordered_by'], 'username'):
                    payload_order_data['ordered_by'] = payload_order_data['ordered_by'].username

                payload = {
                    'order_data': payload_order_data,
                    'items_data': final_items_data
                }
                
                outbox = SyncOutbox.objects.create(
                    entity_type='order',
                    entity_id=order_id,
                    operation='create',
                    target_system='openemr',
                    payload=payload,
                    status='pending'
                )
                persistence_status["openemr_sync_outbox"] = f"대기중 ({outbox.outbox_id})"

                # 3. Async Task
                from .tasks import process_sync_outbox
                transaction.on_commit(lambda: process_sync_outbox.delay(str(outbox.outbox_id)))

        except Exception as e:
            logger.error(f"Failed to create order: {str(e)}")
            persistence_status["django_emr_orders,django_emr_order_items"] = f"실패: {str(e)}"
            raise e

        return order, persistence_status

    @staticmethod
    def execute_order(order_id, executed_by, current_version):
        """
        처방 실행 (상태 업데이트)
        - 비관적 락과 낙관적 락을 합쳐서 적용
        """
        try:
            with transaction.atomic():
                # 1. 비관적 락
                order = OrderRepository.get_order_by_id(order_id, for_update=True)
                if not order:
                    raise Exception("처방을 찾을 수 없습니다.")
                
                # 2. 낙관적 락 적용하며 업데이트
                update_data = {
                    'status': 'completed',
                    'executed_at': datetime.now(),
                    'executed_by_id': executed_by
                }
                
                success = OrderRepository.update_order_optimistic(order_id, current_version, update_data)
                if not success:
                    raise Exception("다른 사용자에 의해 처방 상태가 이미 변경되었습니다. (Concurrency Error)")
                
                # [UC07] 처방 실행 완료 알림 발송
                try:
                    from acct.services import AlertService
                    AlertService.send_alert(
                        user_id=order.ordered_by.user_id, # 처방 의사에게 완료 알림 (User Object -> ID extraction)
                        message=f"처방이 실행되었습니다: {order_id}",
                        alert_type='SUCCESS',
                        metadata={'order_id': order_id, 'patient_id': order.patient_id}
                    )
                except Exception as alert_err:
                    logger.warning(f"Failed to send order execution alert: {str(alert_err)}")

                # [UC09] 감사 로그
                from audit.services import AuditService
                AuditService.log_action(
                    user=None,
                    action='EXECUTE',
                    app_label='ocs',
                    model_name='Order',
                    object_id=order_id,
                    change_summary=f"처방 실행 완료: {order_id}"
                )

                return OrderRepository.get_order_by_id(order_id)
        except Exception as e:
            logger.error(f"Order execution failed: {str(e)}")
            raise e

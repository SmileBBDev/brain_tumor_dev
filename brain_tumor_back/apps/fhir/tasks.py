"""
FHIR Celery Tasks

Celery 백그라운드 작업으로 FHIR 동기화 큐를 처리합니다.
- OAuth 2.0 토큰 관리 (Redis 캐싱)
- FHIR 서버로 리소스 전송
- 재시도 로직 및 에러 핸들링
"""
import logging
import json
import requests
from datetime import datetime, timedelta
from typing import Dict, Optional
from celery import shared_task
from django.conf import settings
from django.core.cache import cache
from django.db import models as django_models
from django.utils import timezone

from .models import FHIRSyncQueue, FHIRResourceMap

logger = logging.getLogger(__name__)


class FHIRSyncError(Exception):
    """FHIR 동기화 에러"""
    pass


def get_oauth_token() -> Optional[str]:
    """
    FHIR 서버 OAuth 2.0 액세스 토큰 가져오기 (Redis 캐시 사용)

    Returns:
        액세스 토큰 (str) 또는 None
    """
    # Redis 캐시에서 토큰 확인
    cache_key = 'fhir_oauth_token'
    cached_token = cache.get(cache_key)

    if cached_token:
        logger.debug("Using cached OAuth token")
        return cached_token

    # 새 토큰 요청
    token_url = getattr(settings, 'FHIR_OAUTH_TOKEN_URL', None)
    client_id = getattr(settings, 'FHIR_OAUTH_CLIENT_ID', None)
    client_secret = getattr(settings, 'FHIR_OAUTH_CLIENT_SECRET', None)

    if not all([token_url, client_id, client_secret]):
        logger.warning("FHIR OAuth credentials not configured")
        return None

    try:
        response = requests.post(
            token_url,
            data={
                'grant_type': 'client_credentials',
                'client_id': client_id,
                'client_secret': client_secret,
                'scope': 'system/*.read system/*.write'
            },
            timeout=10
        )
        response.raise_for_status()

        token_data = response.json()
        access_token = token_data.get('access_token')
        expires_in = token_data.get('expires_in', 3600)  # 기본 1시간

        # Redis에 캐싱 (만료 시간 90%로 설정하여 안전 마진 확보)
        cache_timeout = int(expires_in * 0.9)
        cache.set(cache_key, access_token, timeout=cache_timeout)

        logger.info(f"Obtained new OAuth token (expires in {expires_in}s)")
        return access_token

    except requests.RequestException as e:
        logger.error(f"Failed to obtain OAuth token: {e}")
        return None


def convert_cdss_to_fhir(resource_type: str, cdss_id: str, payload: Dict) -> Dict:
    """
    CDSS 리소스를 FHIR 리소스로 변환

    Args:
        resource_type: FHIR 리소스 타입 (예: 'ImagingStudy', 'Patient')
        cdss_id: CDSS 내부 리소스 ID
        payload: Signal에서 전달된 추가 데이터

    Returns:
        FHIR 리소스 JSON (dict)

    Raises:
        FHIRSyncError: 변환 실패 시
    """
    try:
        # ImagingStudy 변환
        if resource_type == 'ImagingStudy':
            from ris.models import RadiologyStudy
            from .converters_extended import ImagingStudyConverter

            study = RadiologyStudy.objects.get(study_id=cdss_id)
            return ImagingStudyConverter.to_fhir(study)

        # Patient 변환
        elif resource_type == 'Patient':
            from emr.models import PatientCache
            from .converters import PatientConverter

            patient = PatientCache.objects.get(patient_id=cdss_id)
            return PatientConverter.to_fhir(patient)

        # Observation 변환
        elif resource_type == 'Observation':
            from lis.models import LabResult
            from .converters import ObservationConverter

            lab_result = LabResult.objects.get(result_id=cdss_id)
            return ObservationConverter.to_fhir(lab_result)

        # 기타 리소스 타입 추가 가능...
        else:
            raise FHIRSyncError(f"Unsupported resource type: {resource_type}")

    except Exception as e:
        logger.error(f"Failed to convert {resource_type}/{cdss_id} to FHIR: {e}")
        raise FHIRSyncError(f"FHIR conversion failed: {e}")


def send_fhir_resource(resource_type: str, fhir_payload: Dict, access_token: Optional[str] = None) -> Dict:
    """
    FHIR 서버로 리소스 전송 (POST 또는 PUT)

    Args:
        resource_type: FHIR 리소스 타입 (예: 'Patient', 'Observation')
        fhir_payload: FHIR 리소스 JSON
        access_token: OAuth 2.0 액세스 토큰 (선택)

    Returns:
        FHIR 서버 응답 (dict)

    Raises:
        FHIRSyncError: 동기화 실패 시
    """
    fhir_server_url = getattr(settings, 'FHIR_SERVER_URL', 'http://localhost:8080/fhir')
    resource_id = fhir_payload.get('id')

    # 헤더 설정
    headers = {
        'Content-Type': 'application/fhir+json',
        'Accept': 'application/fhir+json'
    }

    if access_token:
        headers['Authorization'] = f'Bearer {access_token}'

    try:
        # 리소스 ID가 있으면 PUT (업데이트), 없으면 POST (생성)
        if resource_id:
            url = f"{fhir_server_url}/{resource_type}/{resource_id}"
            response = requests.put(url, json=fhir_payload, headers=headers, timeout=30)
        else:
            url = f"{fhir_server_url}/{resource_type}"
            response = requests.post(url, json=fhir_payload, headers=headers, timeout=30)

        response.raise_for_status()

        return response.json()

    except requests.HTTPError as e:
        error_msg = f"FHIR server HTTP error: {e.response.status_code} - {e.response.text}"
        logger.error(error_msg)
        raise FHIRSyncError(error_msg)

    except requests.RequestException as e:
        error_msg = f"FHIR server request failed: {str(e)}"
        logger.error(error_msg)
        raise FHIRSyncError(error_msg)


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def sync_fhir_resource(self, queue_id: int):
    """
    FHIR 동기화 큐 항목 하나를 처리하는 Celery 태스크

    Args:
        queue_id: FHIRSyncQueue 레코드 ID (queue_id 필드)

    Returns:
        처리 결과 (dict)
    """
    try:
        # 큐 항목 조회
        queue_item = FHIRSyncQueue.objects.get(queue_id=queue_id)

        # 이미 처리 완료된 경우
        if queue_item.status == 'completed':
            logger.info(f"Queue item {queue_id} already completed")
            return {'status': 'already_completed', 'queue_id': queue_id}

        # 처리 중으로 상태 변경
        queue_item.mark_as_processing()
        queue_item.retry_count += 1
        queue_item.save(update_fields=['retry_count', 'updated_at'])

        resource_map = queue_item.resource_map
        logger.info(f"Processing FHIR sync queue {queue_id}: {resource_map.resource_type} {resource_map.cdss_id}")

        # FHIR Converter로 리소스 변환 (payload에서 CDSS 데이터 가져와서 변환)
        fhir_payload = convert_cdss_to_fhir(resource_map.resource_type, resource_map.cdss_id, queue_item.payload)

        # OAuth 토큰 가져오기
        access_token = get_oauth_token()

        # FHIR 서버로 전송
        response_data = send_fhir_resource(
            resource_type=resource_map.resource_type,
            fhir_payload=fhir_payload,
            access_token=access_token
        )

        # FHIR 서버 응답에서 FHIR ID 추출
        fhir_id = response_data.get('id')

        if not fhir_id:
            raise FHIRSyncError("FHIR server response missing 'id' field")

        # FHIRResourceMap 업데이트 (FHIR ID 저장)
        resource_map.fhir_id = fhir_id
        resource_map.last_synced_at = timezone.now()
        resource_map.save()

        # 큐 항목 완료 처리
        queue_item.mark_as_completed()

        logger.info(f"FHIR sync completed: {resource_map.resource_type}/{fhir_id}")

        return {
            'status': 'success',
            'queue_id': queue_id,
            'resource_type': resource_map.resource_type,
            'cdss_id': resource_map.cdss_id,
            'fhir_id': fhir_id,
        }

    except FHIRSyncQueue.DoesNotExist:
        error_msg = f"Queue item {queue_id} not found"
        logger.error(error_msg)
        return {'status': 'error', 'queue_id': queue_id, 'error': error_msg}

    except FHIRSyncError as e:
        # FHIR 동기화 에러 - 재시도
        error_msg = str(e)
        logger.warning(f"FHIR sync error for queue {queue_id}: {error_msg}")

        # 큐 항목 에러 상태로 변경
        queue_item.status = 'failed'
        queue_item.error_message = error_msg
        queue_item.save()

        # Celery 재시도 (최대 3회)
        if self.request.retries < self.max_retries:
            logger.info(f"Retrying queue {queue_id} (attempt {self.request.retries + 1}/{self.max_retries})")
            raise self.retry(exc=e)
        else:
            logger.error(f"Max retries reached for queue {queue_id}")
            return {
                'status': 'failed',
                'queue_id': queue_id,
                'error': error_msg,
                'retries': self.request.retries
            }

    except Exception as e:
        # 예상치 못한 에러
        error_msg = f"Unexpected error: {str(e)}"
        logger.error(f"Queue {queue_id} failed: {error_msg}", exc_info=True)

        # 큐 항목 에러 상태로 변경
        queue_item.status = 'failed'
        queue_item.error_message = error_msg
        queue_item.save()

        return {
            'status': 'error',
            'queue_id': queue_id,
            'error': error_msg
        }


@shared_task
def process_fhir_sync_queue():
    """
    FHIR 동기화 큐 전체를 주기적으로 처리하는 Celery Beat 태스크

    - 'pending' 상태 항목 우선 처리
    - 우선순위(priority) 순으로 정렬
    - 각 항목을 개별 Celery 태스크로 비동기 처리

    Returns:
        처리 통계 (dict)
    """
    logger.info("Starting FHIR sync queue processing")

    # Pending 상태 큐 항목 조회 (우선순위 높은 것부터, priority: 1=highest, 10=lowest)
    pending_items = FHIRSyncQueue.objects.filter(
        status='pending'
    ).order_by('priority', 'scheduled_at')[:100]  # 한 번에 최대 100개 처리

    # Failed 상태이지만 재시도 가능한 항목 조회
    failed_items = FHIRSyncQueue.objects.filter(
        status='failed',
        retry_count__lt=django_models.F('max_retries')
    ).order_by('priority', 'scheduled_at')[:50]  # 한 번에 최대 50개 재시도

    total_items = list(pending_items) + list(failed_items)

    if not total_items:
        logger.info("No pending FHIR sync queue items")
        return {'status': 'no_items', 'count': 0}

    logger.info(f"Found {len(total_items)} items to process ({len(pending_items)} pending, {len(failed_items)} failed)")

    # 각 항목을 개별 Celery 태스크로 처리
    dispatched = 0
    for item in total_items:
        try:
            # 비동기 태스크 디스패치
            sync_fhir_resource.delay(item.queue_id)
            dispatched += 1
        except Exception as e:
            logger.error(f"Failed to dispatch task for queue {item.queue_id}: {e}")

    logger.info(f"Dispatched {dispatched} FHIR sync tasks")

    return {
        'status': 'dispatched',
        'total_items': len(total_items),
        'dispatched': dispatched,
        'pending': len(pending_items),
        'retry': len(failed_items)
    }


@shared_task
def cleanup_old_sync_queue():
    """
    오래된 FHIR 동기화 큐 항목 정리 (Celery Beat 주기적 실행)

    - 완료된 항목: 30일 후 삭제
    - 실패한 항목: 90일 후 삭제

    Returns:
        삭제된 항목 수 (dict)
    """
    logger.info("Starting FHIR sync queue cleanup")

    # 30일 이전 완료 항목 삭제
    completed_cutoff = timezone.now() - timedelta(days=30)
    completed_deleted = FHIRSyncQueue.objects.filter(
        status='completed',
        completed_at__lt=completed_cutoff
    ).delete()[0]

    # 90일 이전 실패 항목 삭제
    failed_cutoff = timezone.now() - timedelta(days=90)
    failed_deleted = FHIRSyncQueue.objects.filter(
        status='failed',
        last_attempted_at__lt=failed_cutoff
    ).delete()[0]

    logger.info(f"Cleanup completed: {completed_deleted} completed, {failed_deleted} failed items deleted")

    return {
        'status': 'completed',
        'completed_deleted': completed_deleted,
        'failed_deleted': failed_deleted,
        'total_deleted': completed_deleted + failed_deleted
    }

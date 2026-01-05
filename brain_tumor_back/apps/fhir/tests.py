"""
FHIR App Tests

FHIR 리소스 변환, 동기화 큐, Celery 태스크 테스트
"""
from django.test import TestCase, TransactionTestCase
from django.utils import timezone
from django.core.cache import cache
from unittest.mock import patch, MagicMock
import json

from emr.models import Patient, Encounter, EncounterDiagnosis, Order
from ris.models import RadiologyOrder, RadiologyStudy
from .models import FHIRResourceMap, FHIRSyncQueue
from .converters import PatientConverter, EncounterConverter, ObservationConverter, DiagnosticReportConverter
from .converters_extended import (
    MedicationRequestConverter,
    ServiceRequestConverter,
    ConditionConverter,
    ImagingStudyConverter,
    ProcedureConverter
)
from .tasks import get_oauth_token, send_fhir_resource, sync_fhir_resource


class PatientConverterTest(TestCase):
    """Patient 컨버터 테스트"""

    def setUp(self):
        """테스트 데이터 생성"""
        self.patient = Patient.objects.create(
            patient_id='TEST001',
            first_name='John',
            last_name='Doe',
            date_of_birth='1990-01-01',
            gender='M',
            phone='010-1234-5678',
            email='john.doe@example.com',
            address='Seoul, Korea'
        )

    def test_patient_to_fhir(self):
        """Patient → FHIR Resource 변환 테스트"""
        fhir_resource = PatientConverter.to_fhir(self.patient)

        self.assertEqual(fhir_resource['resourceType'], 'Patient')
        self.assertEqual(fhir_resource['id'], 'TEST001')
        self.assertEqual(fhir_resource['gender'], 'male')
        self.assertEqual(fhir_resource['birthDate'], '1990-01-01')
        self.assertEqual(fhir_resource['name'][0]['family'], 'Doe')
        self.assertEqual(fhir_resource['name'][0]['given'], ['John'])
        self.assertIn('telecom', fhir_resource)
        self.assertIn('address', fhir_resource)

    def test_patient_identifier(self):
        """Patient identifier 테스트"""
        fhir_resource = PatientConverter.to_fhir(self.patient)

        self.assertIn('identifier', fhir_resource)
        self.assertEqual(len(fhir_resource['identifier']), 1)
        self.assertEqual(fhir_resource['identifier'][0]['value'], 'TEST001')


class MedicationRequestConverterTest(TestCase):
    """MedicationRequest 컨버터 테스트"""

    def setUp(self):
        """테스트 데이터 생성"""
        self.patient = Patient.objects.create(
            patient_id='TEST001',
            first_name='John',
            last_name='Doe',
            date_of_birth='1990-01-01',
            gender='M'
        )
        self.encounter = Encounter.objects.create(
            encounter_id='ENC001',
            patient=self.patient,
            encounter_type='outpatient',
            status='in_progress',
            start_time=timezone.now()
        )
        self.order = Order.objects.create(
            order_id='ORD001',
            patient=self.patient,
            encounter_id='ENC001',
            order_type='medication',
            status='pending',
            urgency='routine',
            doctor_id='DOC001',
            instructions='Take 1 tablet daily after meal'
        )

    def test_medication_request_to_fhir(self):
        """MedicationRequest → FHIR Resource 변환 테스트"""
        fhir_resource = MedicationRequestConverter.to_fhir(self.order)

        self.assertEqual(fhir_resource['resourceType'], 'MedicationRequest')
        self.assertEqual(fhir_resource['id'], 'ORD001')
        self.assertEqual(fhir_resource['status'], 'active')
        self.assertEqual(fhir_resource['intent'], 'order')
        self.assertEqual(fhir_resource['priority'], 'routine')
        self.assertIn('subject', fhir_resource)
        self.assertIn('medicationCodeableConcept', fhir_resource)
        self.assertIn('dosageInstruction', fhir_resource)


class ConditionConverterTest(TestCase):
    """Condition 컨버터 테스트"""

    def setUp(self):
        """테스트 데이터 생성"""
        self.patient = Patient.objects.create(
            patient_id='TEST001',
            first_name='John',
            last_name='Doe',
            date_of_birth='1990-01-01',
            gender='M'
        )
        self.encounter = Encounter.objects.create(
            encounter_id='ENC001',
            patient=self.patient,
            encounter_type='outpatient',
            status='in_progress',
            start_time=timezone.now()
        )
        self.diagnosis = EncounterDiagnosis.objects.create(
            encounter=self.encounter,
            diag_code='I10',
            diagnosis_name='Essential hypertension',
            priority=1,
            comments='Primary diagnosis'
        )

    def test_condition_to_fhir(self):
        """Condition → FHIR Resource 변환 테스트"""
        fhir_resource = ConditionConverter.to_fhir(self.diagnosis)

        self.assertEqual(fhir_resource['resourceType'], 'Condition')
        self.assertIn('clinicalStatus', fhir_resource)
        self.assertIn('verificationStatus', fhir_resource)
        self.assertEqual(fhir_resource['code']['coding'][0]['code'], 'I10')
        self.assertEqual(fhir_resource['code']['coding'][0]['display'], 'Essential hypertension')
        self.assertIn('subject', fhir_resource)
        self.assertIn('encounter', fhir_resource)


class ImagingStudyConverterTest(TestCase):
    """ImagingStudy 컨버터 테스트"""

    def setUp(self):
        """테스트 데이터 생성"""
        self.study = RadiologyStudy.objects.create(
            study_id=1,
            study_instance_uid='1.2.840.113619.2.1.1.1',
            patient_id='TEST001',
            patient_name='John Doe',
            study_date='20250101',
            study_time='120000',
            modality='CT',
            study_description='CT Brain without contrast',
            num_series=3,
            num_instances=150,
            referring_physician='Dr. Smith'
        )

    def test_imaging_study_to_fhir(self):
        """ImagingStudy → FHIR Resource 변환 테스트"""
        fhir_resource = ImagingStudyConverter.to_fhir(self.study)

        self.assertEqual(fhir_resource['resourceType'], 'ImagingStudy')
        self.assertEqual(fhir_resource['status'], 'available')
        self.assertEqual(fhir_resource['numberOfSeries'], 3)
        self.assertEqual(fhir_resource['numberOfInstances'], 150)
        self.assertIn('identifier', fhir_resource)
        self.assertIn('modality', fhir_resource)
        self.assertIn('endpoint', fhir_resource)


class FHIRResourceMapTest(TestCase):
    """FHIRResourceMap 모델 테스트"""

    def test_create_resource_map(self):
        """리소스 맵 생성 테스트"""
        resource_map = FHIRResourceMap.objects.create(
            cdss_id='TEST001',
            fhir_id='FHIR001',
            resource_type='Patient'
        )

        self.assertEqual(resource_map.cdss_id, 'TEST001')
        self.assertEqual(resource_map.fhir_id, 'FHIR001')
        self.assertEqual(resource_map.resource_type, 'Patient')
        self.assertIsNotNone(resource_map.last_synced_at)

    def test_unique_constraint(self):
        """Unique constraint 테스트"""
        FHIRResourceMap.objects.create(
            cdss_id='TEST001',
            fhir_id='FHIR001',
            resource_type='Patient'
        )

        # 동일한 cdss_id + resource_type는 생성 불가
        with self.assertRaises(Exception):
            FHIRResourceMap.objects.create(
                cdss_id='TEST001',
                fhir_id='FHIR002',
                resource_type='Patient'
            )


class FHIRSyncQueueTest(TestCase):
    """FHIRSyncQueue 모델 테스트"""

    def test_create_sync_queue(self):
        """동기화 큐 생성 테스트"""
        queue_item = FHIRSyncQueue.objects.create(
            cdss_id='TEST001',
            resource_type='Patient',
            fhir_payload={'resourceType': 'Patient', 'id': 'TEST001'},
            priority=1
        )

        self.assertEqual(queue_item.status, 'pending')
        self.assertEqual(queue_item.retry_count, 0)
        self.assertEqual(queue_item.priority, 1)
        self.assertIsNone(queue_item.error_message)

    def test_queue_ordering(self):
        """큐 우선순위 정렬 테스트"""
        FHIRSyncQueue.objects.create(
            cdss_id='TEST001',
            resource_type='Patient',
            fhir_payload={},
            priority=2
        )
        FHIRSyncQueue.objects.create(
            cdss_id='TEST002',
            resource_type='Patient',
            fhir_payload={},
            priority=1
        )
        FHIRSyncQueue.objects.create(
            cdss_id='TEST003',
            resource_type='Patient',
            fhir_payload={},
            priority=3
        )

        # 우선순위 높은 순으로 조회
        queue_items = FHIRSyncQueue.objects.filter(status='pending').order_by('-priority')

        self.assertEqual(queue_items[0].cdss_id, 'TEST003')  # priority 3
        self.assertEqual(queue_items[1].cdss_id, 'TEST001')  # priority 2
        self.assertEqual(queue_items[2].cdss_id, 'TEST002')  # priority 1


class CeleryTaskTest(TransactionTestCase):
    """Celery 태스크 테스트"""

    def setUp(self):
        """테스트 데이터 생성"""
        # 캐시 초기화
        cache.clear()

    def test_get_oauth_token_cached(self):
        """OAuth 토큰 캐시 테스트"""
        # 캐시에 토큰 설정
        cache.set('fhir_oauth_token', 'test_token_123', timeout=3600)

        token = get_oauth_token()

        self.assertEqual(token, 'test_token_123')

    @patch('fhir.tasks.requests.post')
    def test_get_oauth_token_new(self, mock_post):
        """OAuth 토큰 신규 발급 테스트"""
        # Mock 응답 설정
        mock_response = MagicMock()
        mock_response.json.return_value = {
            'access_token': 'new_token_456',
            'expires_in': 3600
        }
        mock_response.raise_for_status = MagicMock()
        mock_post.return_value = mock_response

        # settings에 OAuth 설정 추가 (패치)
        with patch('fhir.tasks.getattr') as mock_getattr:
            def getattr_side_effect(obj, key, default=None):
                oauth_settings = {
                    'FHIR_OAUTH_TOKEN_URL': 'http://test/oauth/token',
                    'FHIR_OAUTH_CLIENT_ID': 'test_client',
                    'FHIR_OAUTH_CLIENT_SECRET': 'test_secret'
                }
                return oauth_settings.get(key, default)

            mock_getattr.side_effect = getattr_side_effect

            token = get_oauth_token()

            self.assertEqual(token, 'new_token_456')
            # 캐시에 저장되었는지 확인
            cached_token = cache.get('fhir_oauth_token')
            self.assertEqual(cached_token, 'new_token_456')

    @patch('fhir.tasks.requests.put')
    def test_send_fhir_resource_success(self, mock_put):
        """FHIR 리소스 전송 성공 테스트"""
        # Mock 응답 설정
        mock_response = MagicMock()
        mock_response.json.return_value = {
            'resourceType': 'Patient',
            'id': 'TEST001'
        }
        mock_response.raise_for_status = MagicMock()
        mock_put.return_value = mock_response

        fhir_payload = {
            'resourceType': 'Patient',
            'id': 'TEST001',
            'name': [{'family': 'Doe', 'given': ['John']}]
        }

        result = send_fhir_resource('Patient', fhir_payload)

        self.assertEqual(result['resourceType'], 'Patient')
        self.assertEqual(result['id'], 'TEST001')

    @patch('fhir.tasks.send_fhir_resource')
    @patch('fhir.tasks.get_oauth_token')
    def test_sync_fhir_resource_success(self, mock_get_token, mock_send):
        """FHIR 동기화 태스크 성공 테스트"""
        # Mock 설정
        mock_get_token.return_value = 'test_token'
        mock_send.return_value = {
            'resourceType': 'Patient',
            'id': 'FHIR_TEST001'
        }

        # 큐 항목 생성
        queue_item = FHIRSyncQueue.objects.create(
            cdss_id='TEST001',
            resource_type='Patient',
            fhir_payload={'resourceType': 'Patient', 'id': 'TEST001'}
        )

        # 태스크 실행
        result = sync_fhir_resource(queue_item.id)

        self.assertEqual(result['status'], 'success')
        self.assertEqual(result['fhir_id'], 'FHIR_TEST001')

        # 큐 항목 상태 확인
        queue_item.refresh_from_db()
        self.assertEqual(queue_item.status, 'completed')
        self.assertIsNotNone(queue_item.completed_at)

        # 리소스 맵 생성 확인
        resource_map = FHIRResourceMap.objects.get(cdss_id='TEST001', resource_type='Patient')
        self.assertEqual(resource_map.fhir_id, 'FHIR_TEST001')


class FHIRAPITest(TestCase):
    """FHIR API 엔드포인트 테스트"""

    def setUp(self):
        """테스트 데이터 생성"""
        self.patient = Patient.objects.create(
            patient_id='TEST001',
            first_name='John',
            last_name='Doe',
            date_of_birth='1990-01-01',
            gender='M'
        )

    def test_get_patient_fhir(self):
        """Patient FHIR 리소스 조회 API 테스트"""
        response = self.client.get(f'/api/fhir/Patient/{self.patient.patient_id}/')

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data['resourceType'], 'Patient')
        self.assertEqual(data['id'], 'TEST001')

    def test_create_fhir_sync_task(self):
        """FHIR 동기화 작업 생성 API 테스트"""
        payload = {
            'resource_type': 'Patient',
            'cdss_id': 'TEST001',
            'priority': 1
        }

        response = self.client.post(
            '/api/fhir/sync/',
            data=json.dumps(payload),
            content_type='application/json'
        )

        self.assertEqual(response.status_code, 201)
        data = response.json()
        self.assertEqual(data['resource_type'], 'Patient')
        self.assertEqual(data['cdss_id'], 'TEST001')
        self.assertEqual(data['status'], 'pending')

        # 큐에 생성되었는지 확인
        queue_item = FHIRSyncQueue.objects.get(cdss_id='TEST001', resource_type='Patient')
        self.assertEqual(queue_item.status, 'pending')

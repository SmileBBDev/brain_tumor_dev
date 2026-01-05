"""
OpenEMR 연동 및 Write-Through 패턴 유닛 테스트

이 테스트 모듈은 다음 항목을 검증합니다:
1. OpenEMRClient (HTTP 연동)
2. EMR Views (Basic Endpoints)
3. EMR CRUD (Service Layer Mocking)
4. Write-Through Caching Pattern (New)

주의: IntegrationTest는 실제 서버 부재 시 스킵 처리함.
"""

from django.test import TestCase, Client
from unittest.mock import patch, Mock, MagicMock
import json
import requests
import unittest
from .openemr_client import OpenEMRClient
from .models import PatientCache, Encounter, Order, OrderItem
from django.utils import timezone

class OpenEMRClientTestCase(TestCase):
    """OpenEMRClient 클래스 유닛 테스트"""

    def setUp(self):
        self.client = OpenEMRClient(base_url="http://localhost:80")

    @patch('requests.Session.get')
    def test_health_check_success(self, mock_get):
        """서버 상태 확인 성공 테스트"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_get.return_value = mock_response

        result = self.client.health_check()
        self.assertEqual(result["status"], "healthy")

    @patch('requests.Session.get')
    def test_health_check_failure(self, mock_get):
        """서버 상태 확인 실패 테스트"""
        mock_get.side_effect = requests.RequestException("Connection failed")
        result = self.client.health_check()
        self.assertEqual(result["status"], "error")

    @patch('requests.Session.post')
    def test_authenticate_success(self, mock_post):
        """인증 성공 테스트"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "access_token": "test_token",
            "token_type": "Bearer",
            "expires_in": 3600
        }
        mock_post.return_value = mock_response

        result = self.client.authenticate("admin", "pass")
        self.assertTrue(result["success"])

    @patch('requests.Session.get')
    def test_get_patient_by_id(self, mock_get):
        """특정 환자 조회 테스트"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "resourceType": "Patient",
            "id": "1",
            "name": [{"given": ["John"], "family": "Doe"}]
        }
        mock_get.return_value = mock_response

        result = self.client.get_patient("1")
        self.assertEqual(result["id"], "1")


class EMRViewsTestCase(TestCase):
    """EMR Django views API 엔드포인트 테스트"""

    def setUp(self):
        self.client = Client()

    @patch('emr.views.client')
    def test_health_check_endpoint(self, mock_client):
        """Health check 엔드포인트 테스트"""
        mock_client.health_check.return_value = {"status": "healthy", "status_code": 200}
        response = self.client.get('/api/emr/health/')
        self.assertEqual(response.status_code, 200)

    @patch('emr.views.client')
    def test_list_patients_endpoint(self, mock_client):
        """환자 목록 조회 엔드포인트 테스트"""
        mock_client.get_patients.return_value = []
        response = self.client.get('/api/emr/patients/?limit=10')
        self.assertEqual(response.status_code, 200)


@unittest.skip("실제 OpenEMR 서버가 없어 localhost 연결 에러 발생하므로 스킵")
class EMRIntegrationTestCase(TestCase):
    """OpenEMR 통합 테스트 (실제 서버 필요)"""
    pass


class EMRCRUDTestCase(TestCase):
    """
    CRUD 기능 (Patient, Order, OrderItem) 유닛 테스트
    - OpenEMRPatientRepository Mocking 필수 (DB 연결 에러 방지)
    """
    
    def setUp(self):
        self.client = Client()
        # Create Dummy User for FK tests
        from django.contrib.auth import get_user_model
        User = get_user_model()
        self.user = User.objects.create_user(username='doctor_1', email='doc@test.com', password='password')
        
        # Create MedicationMaster
        from ocs.models import MedicationMaster
        MedicationMaster.objects.create(
            drug_code="D001",
            drug_name="Tylenol"
        )
        
        self.patient_data = {
            "family_name": "Test",
            "given_name": "User",
            "birth_date": "1990-01-01",
            "gender": "male",
            "phone": "010-1234-5678",
            "email": "test@example.com"
        }

    def test_create_patient(self):
        """환자 생성 테스트"""
        # Outbox Pattern이 적용되어 있으므로 Repository Lock Mocking 불필요
        response = self.client.post('/api/emr/patients/', data=self.patient_data, content_type='application/json')
        self.assertEqual(response.status_code, 201)
        self.assertTrue(PatientCache.objects.filter(family_name="Test").exists())

    def test_create_order_with_items(self):
        """처방 생성 및 항목 자동 생성 테스트"""
        
        # 1. 환자 생성
        p_res = self.client.post('/api/emr/patients/', data=self.patient_data, content_type='application/json')
        patient_id = p_res.json()['data']['patient_id']

        # 2. 처방 생성
        order_data = {
            "patient": patient_id,
            "order_type": "medication",
            "urgency": "routine",
            "ordered_by": self.user.pk,  # Use User ID
            "order_items": [
                {
                    "drug_code": "D001",
                    "drug_name": "Tylenol",
                    "dosage": "500mg",
                    "frequency": "BID",
                    "duration": "3 days"
                }
            ]
        }
        response = self.client.post('/api/emr/orders/', data=order_data, content_type='application/json')
        if response.status_code != 201:
             print(f"DEBUG Error Response: {response.json()}")
        self.assertEqual(response.status_code, 201)
        
        # 3. 항목 생성 확인
        order_id = response.json()['order_id']
        self.assertEqual(OrderItem.objects.filter(item_id__startswith=f"OI-{order_id}").count(), 1)


class OutboxPatternTestCase(TestCase):
    """
    [아키텍처 규칙 검증] Outbox 패턴 테스트
    
    규칙:
    1. 데이터 생성/수정 시 SyncOutbox 레코드가 함께 생성되어야 함 (Transaction 보장)
    2. 생성된 Outbox 상태는 'pending'이어야 함
    """

    def setUp(self):
        self.client = Client()
        self.patient_data = {
            "family_name": "Target",
            "given_name": "Patient",
            "birth_date": "2000-01-01",
            "gender": "male",
            "phone": "010-0000-0000",
            "email": "outbox@example.com"
        }

    def test_create_patient_creates_outbox(self):
        """
        Scenario 1: 환자 생성 시 Outbox 레코드가 자동 생성되어야 함
        """
        # When: API 호출
        response = self.client.post(
            '/api/emr/patients/', 
            data=self.patient_data, 
            content_type='application/json'
        )

        # Then: 201 Created
        # Then: 201 Created
        if response.status_code != 201:
            print(f"DEBUG Error Response: {response.json()}")
        self.assertEqual(response.status_code, 201)
        patient_id = response.json()['data']['patient_id']

        # Verify Outbox
        from .models import SyncOutbox
        outbox = SyncOutbox.objects.filter(
            entity_type='patient',
            entity_id=patient_id,
            operation='create'
        ).first()

        self.assertIsNotNone(outbox, "Outbox record should be created")
        self.assertEqual(outbox.status, 'pending')
        self.assertEqual(outbox.target_system, 'openemr')

    def test_update_patient_creates_outbox(self):
        """
        Scenario 2: 환자 수정 시 Outbox 레코드가 자동 생성되어야 함
        """
        # Given: 환자 생성
        from .models import PatientCache
        patient = PatientCache.objects.create(
            patient_id="P-TEST-UPDATE",
            family_name="Target", 
            given_name="Patient",
            birth_date="2000-01-01",
            gender="male"
        )
        
        update_data = {"phone": "010-9999-9999"}
        url = f'/api/emr/patients/{patient.patient_id}/'

        # When: API 호출 (PATCH)
        response = self.client.patch(
            url,
            data=update_data,
            content_type='application/json'
        )

        # Then: 200 OK
        self.assertEqual(response.status_code, 200)

        # Verify Outbox
        from .models import SyncOutbox
        outbox = SyncOutbox.objects.filter(
            entity_type='patient',
            entity_id=patient.patient_id,
            operation='update'
        ).first()

        self.assertIsNotNone(outbox)
        self.assertEqual(outbox.status, 'pending')


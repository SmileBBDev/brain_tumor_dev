"""
OpenEMR FHIR API Client

OpenEMR의 FHIR R4 API와 통신하는 클라이언트입니다.
"""

import requests
import logging
from typing import Optional, Dict, Any
from django.conf import settings

logger = logging.getLogger(__name__)


class OpenEMRClient:
    """
    OpenEMR FHIR API 클라이언트

    OpenEMR의 FHIR R4 엔드포인트와 통신하여 환자 상세 정보를 관리합니다.

    Attributes:
        base_url: OpenEMR FHIR API base URL
        client_id: OAuth 2.0 Client ID
        client_secret: OAuth 2.0 Client Secret
    """

    def __init__(
        self,
        base_url: Optional[str] = None,
        client_id: Optional[str] = None,
        client_secret: Optional[str] = None
    ):
        """
        Initialize OpenEMR FHIR API client

        Args:
            base_url: OpenEMR FHIR API URL (default: settings.OPENEMR_FHIR_URL)
            client_id: OAuth client ID (default: settings.OPENEMR_CLIENT_ID)
            client_secret: OAuth client secret (default: settings.OPENEMR_CLIENT_SECRET)
        """
        self.base_url = base_url or getattr(
            settings,
            'OPENEMR_FHIR_URL',
            'http://localhost:80/apis/default/fhir'
        )
        self.client_id = client_id or getattr(settings, 'OPENEMR_CLIENT_ID', '')
        self.client_secret = client_secret or getattr(settings, 'OPENEMR_CLIENT_SECRET', '')

        # OAuth 토큰 (TODO: 실제 OAuth 구현 시 활성화)
        self._access_token: Optional[str] = None

    def get_access_token(self) -> Optional[str]:
        """
        Get OAuth2 access token using Client Credentials Flow
        """
        if self._access_token:
            return self._access_token
            
        # Construct Token URL from Base URL
        # base_url: htp://host/apis/default/fhir -> token_url: http://host/oauth2/default/token
        token_url = self.base_url.replace('/apis/default/fhir', '/oauth2/default/token')
        print(f"DEBUG: Token URL: {token_url}")
        
        try:
            logger.info(f"Requesting OpenEMR Token from {token_url} (Client: {self.client_id})")
            # Use Body Auth (client_secret_post)
            response = requests.post(
                token_url,
                data={
                    'grant_type': 'client_credentials',
                    'client_id': self.client_id,
                    'client_secret': self.client_secret,
                    # 'scope': 'system/Patient.read'
                },
                # auth=(self.client_id, self.client_secret), # Disable Basic Auth
                headers={'Content-Type': 'application/x-www-form-urlencoded'},
                timeout=10
            )
            response.raise_for_status()
            token_data = response.json()
            self._access_token = token_data.get('access_token')
            logger.info("✓ OpenEMR Access Token retrieved successfully")
            return self._access_token
        except Exception as e:
            logger.error(f"✗ Failed to retrieve OpenEMR Access Token: {str(e)}")
            if hasattr(e, 'response') and e.response is not None:
                logger.error(f"Response: {e.response.text}")
            return None

    def _get_headers(self) -> Dict[str, str]:
        """
        Get HTTP headers for API requests
        """
        headers = {
            'Content-Type': 'application/fhir+json',
            'Accept': 'application/fhir+json',
        }

        # Ensure token is loaded
        if not self._access_token:
            self.get_access_token()

        # Add Authorization header
        if self._access_token:
            headers['Authorization'] = f'Bearer {self._access_token}'
        else:
            logger.warning("Requesting OpenEMR API without Access Token")

        return headers

    def _request(
        self,
        method: str,
        endpoint: str,
        data: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Make HTTP request to OpenEMR FHIR API

        Args:
            method: HTTP method (GET, POST, PUT, DELETE)
            endpoint: API endpoint (e.g., 'Patient', 'Patient/123')
            data: Request body (for POST/PUT)
            params: Query parameters

        Returns:
            Response JSON or None if request failed

        Raises:
            requests.exceptions.RequestException: HTTP request error
        """
        url = f"{self.base_url}/{endpoint}"
        headers = self._get_headers()

        try:
            response = requests.request(
                method=method,
                url=url,
                headers=headers,
                json=data,
                params=params,
                timeout=30
            )

            # HTTP error 체크
            response.raise_for_status()

            # 204 No Content는 빈 딕셔너리 반환
            if response.status_code == 204:
                return {}

            return response.json()

        except requests.exceptions.RequestException as e:
            logger.error(f"OpenEMR API request failed: {method} {url} - {str(e)}")
            if hasattr(e, 'response') and e.response is not None:
                logger.error(f"Response: {e.response.text}")
            raise

    # ============================================
    # Patient Resources
    # ============================================

    def create_patient(self, patient_resource: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Create a new Patient resource in OpenEMR

        Args:
            patient_resource: FHIR Patient resource (dict)

        Returns:
            Created Patient resource with ID, or None if failed
        """
        try:
            result = self._request('POST', 'Patient', data=patient_resource)
            logger.info(f"✓ OpenEMR Patient created: {result.get('id')}")
            return result
        except Exception as e:
            logger.error(f"✗ Failed to create OpenEMR Patient: {str(e)}")
            return None

    def get_patient(self, patient_id: str) -> Optional[Dict[str, Any]]:
        """
        Get Patient resource by ID from OpenEMR

        Args:
            patient_id: OpenEMR Patient ID (FHIR resource ID)

        Returns:
            Patient resource, or None if not found
        """
        try:
            result = self._request('GET', f'Patient/{patient_id}')
            logger.info(f"✓ OpenEMR Patient retrieved: {patient_id}")
            return result
        except Exception as e:
            logger.error(f"✗ Failed to get OpenEMR Patient {patient_id}: {str(e)}")
            return None

    def update_patient(
        self,
        patient_id: str,
        patient_resource: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """
        Update existing Patient resource in OpenEMR

        Args:
            patient_id: OpenEMR Patient ID
            patient_resource: Updated FHIR Patient resource

        Returns:
            Updated Patient resource, or None if failed
        """
        try:
            result = self._request('PUT', f'Patient/{patient_id}', data=patient_resource)
            logger.info(f"✓ OpenEMR Patient updated: {patient_id}")
            return result
        except Exception as e:
            logger.error(f"✗ Failed to update OpenEMR Patient {patient_id}: {str(e)}")
            return None

    def delete_patient(self, patient_id: str) -> bool:
        """
        Delete Patient resource from OpenEMR

        Args:
            patient_id: OpenEMR Patient ID

        Returns:
            True if deleted successfully, False otherwise
        """
        try:
            self._request('DELETE', f'Patient/{patient_id}')
            logger.info(f"✓ OpenEMR Patient deleted: {patient_id}")
            return True
        except Exception as e:
            logger.error(f"✗ Failed to delete OpenEMR Patient {patient_id}: {str(e)}")
            return False

    def search_patients(self, params: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Search Patient resources in OpenEMR

        Args:
            params: Search parameters (e.g., {'name': 'John', 'birthdate': '1990-01-01'})

        Returns:
            FHIR Bundle with search results, or None if failed
        """
        try:
            result = self._request('GET', 'Patient', params=params)
            logger.info(f"✓ OpenEMR Patient search completed")
            return result
        except Exception as e:
            logger.error(f"✗ Failed to search OpenEMR Patients: {str(e)}")
            return None

    # ============================================
    # Encounter Resources
    # ============================================

    def create_encounter(self, encounter_resource: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Create a new Encounter resource in OpenEMR

        Args:
            encounter_resource: FHIR Encounter resource

        Returns:
            Created Encounter resource, or None if failed
        """
        try:
            result = self._request('POST', 'Encounter', data=encounter_resource)
            logger.info(f"✓ OpenEMR Encounter created: {result.get('id')}")
            return result
        except Exception as e:
            logger.error(f"✗ Failed to create OpenEMR Encounter: {str(e)}")
            return None

    def get_encounter(self, encounter_id: str) -> Optional[Dict[str, Any]]:
        """
        Get Encounter resource by ID from OpenEMR

        Args:
            encounter_id: OpenEMR Encounter ID

        Returns:
            Encounter resource, or None if not found
        """
        try:
            result = self._request('GET', f'Encounter/{encounter_id}')
            logger.info(f"✓ OpenEMR Encounter retrieved: {encounter_id}")
            return result
        except Exception as e:
            logger.error(f"✗ Failed to get OpenEMR Encounter {encounter_id}: {str(e)}")
            return None

    def update_encounter(
        self,
        encounter_id: str,
        encounter_resource: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """
        Update existing Encounter resource in OpenEMR

        Args:
            encounter_id: OpenEMR Encounter ID
            encounter_resource: Updated FHIR Encounter resource

        Returns:
            Updated Encounter resource, or None if failed
        """
        try:
            result = self._request('PUT', f'Encounter/{encounter_id}', data=encounter_resource)
            logger.info(f"✓ OpenEMR Encounter updated: {encounter_id}")
            return result
        except Exception as e:
            logger.error(f"✗ Failed to update OpenEMR Encounter {encounter_id}: {str(e)}")
            return None

    # ============================================
    # MedicationRequest Resources (처방)
    # ============================================

    def create_medication_request(
        self,
        medication_request: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """
        Create a new MedicationRequest resource in OpenEMR

        Args:
            medication_request: FHIR MedicationRequest resource

        Returns:
            Created MedicationRequest resource, or None if failed
        """
        try:
            result = self._request('POST', 'MedicationRequest', data=medication_request)
            logger.info(f"✓ OpenEMR MedicationRequest created: {result.get('id')}")
            return result
        except Exception as e:
            logger.error(f"✗ Failed to create OpenEMR MedicationRequest: {str(e)}")
            return None

    def get_medication_request(self, request_id: str) -> Optional[Dict[str, Any]]:
        """
        Get MedicationRequest resource by ID from OpenEMR

        Args:
            request_id: OpenEMR MedicationRequest ID

        Returns:
            MedicationRequest resource, or None if not found
        """
        try:
            result = self._request('GET', f'MedicationRequest/{request_id}')
            logger.info(f"✓ OpenEMR MedicationRequest retrieved: {request_id}")
            return result
        except Exception as e:
            logger.error(f"✗ Failed to get OpenEMR MedicationRequest {request_id}: {str(e)}")
            return None

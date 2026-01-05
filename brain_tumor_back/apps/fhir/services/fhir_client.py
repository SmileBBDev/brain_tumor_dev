"""
FHIR R4 Client

HAPI FHIR 서버와 통신하는 클라이언트
"""

import requests
import logging

logger = logging.getLogger(__name__)


class FHIRClient:
    """FHIR R4 API Client"""

    def __init__(self, base_url):
        """
        Args:
            base_url: FHIR 서버 URL (e.g., http://localhost:8080/fhir)
        """
        self.base_url = base_url.rstrip('/')
        self.session = requests.Session()
        self.session.headers.update({
            'Content-Type': 'application/fhir+json',
            'Accept': 'application/fhir+json',
        })

    def create_resource(self, resource_type, resource_data):
        """
        FHIR 리소스 생성

        Args:
            resource_type: Resource type (e.g., 'Patient', 'MedicationRequest')
            resource_data: Resource data (dict)

        Returns:
            dict: Created resource with ID
        """
        url = f'{self.base_url}/{resource_type}'

        try:
            response = self.session.post(url, json=resource_data, timeout=30)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f'FHIR create failed for {resource_type}: {str(e)}')
            if hasattr(e.response, 'text'):
                logger.error(f'Response: {e.response.text}')
            raise

    def update_resource(self, resource_type, resource_id, resource_data):
        """
        FHIR 리소스 업데이트

        Args:
            resource_type: Resource type
            resource_id: Resource ID
            resource_data: Updated resource data

        Returns:
            dict: Updated resource
        """
        url = f'{self.base_url}/{resource_type}/{resource_id}'

        # ID 필드 추가
        resource_data['id'] = resource_id

        try:
            response = self.session.put(url, json=resource_data, timeout=30)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f'FHIR update failed for {resource_type}/{resource_id}: {str(e)}')
            raise

    def get_resource(self, resource_type, resource_id):
        """
        FHIR 리소스 조회

        Args:
            resource_type: Resource type
            resource_id: Resource ID

        Returns:
            dict: Resource data
        """
        url = f'{self.base_url}/{resource_type}/{resource_id}'

        try:
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f'FHIR get failed for {resource_type}/{resource_id}: {str(e)}')
            raise

    def delete_resource(self, resource_type, resource_id):
        """
        FHIR 리소스 삭제

        Args:
            resource_type: Resource type
            resource_id: Resource ID

        Returns:
            bool: Success
        """
        url = f'{self.base_url}/{resource_type}/{resource_id}'

        try:
            response = self.session.delete(url, timeout=30)
            response.raise_for_status()
            return True
        except requests.exceptions.RequestException as e:
            logger.error(f'FHIR delete failed for {resource_type}/{resource_id}: {str(e)}')
            raise

    def search_resources(self, resource_type, params=None):
        """
        FHIR 리소스 검색

        Args:
            resource_type: Resource type
            params: Search parameters (dict)

        Returns:
            dict: Bundle of resources
        """
        url = f'{self.base_url}/{resource_type}'

        try:
            response = self.session.get(url, params=params, timeout=30)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f'FHIR search failed for {resource_type}: {str(e)}')
            raise

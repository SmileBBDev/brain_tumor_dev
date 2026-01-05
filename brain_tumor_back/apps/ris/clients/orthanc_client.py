import requests
from django.conf import settings
from django.core.cache import cache
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)


class OrthancClient:
    """Orthanc DICOM 서버 클라이언트"""

    # JWT URL 생명주기 설정 (환경변수로 커스터마이징 가능)
    JWT_URL_LIFETIME_HOURS = int(getattr(settings, 'ORTHANC_JWT_LIFETIME_HOURS', 1))  # 기본 1시간

    # Redis 캐시 TTL (생명주기보다 10분 짧게 설정 - 안전 마진)
    CACHE_TTL_SECONDS = (JWT_URL_LIFETIME_HOURS * 3600) - 600  # 1시간 - 10분 = 50분 (3000초)

    def __init__(self):
        self.base_url = settings.ORTHANC_API_URL
        # Orthanc authentication disabled in docker-compose.yml
        self.auth = None
    
    def get(self, endpoint):
        """Generic GET request to Orthanc API"""
        try:
            url = f"{self.base_url}{endpoint}"
            response = requests.get(url, auth=self.auth, timeout=10)
            response.raise_for_status()
            return {'success': True, 'data': response.json()}
        except requests.RequestException as e:
            logger.error(f"Orthanc GET {endpoint} failed: {e}")
            return {'success': False, 'error': str(e)}

    def health_check(self):
        """Orthanc 서버 연결 확인"""
        try:
            url = f"{self.base_url}/system"
            response = requests.get(url, auth=self.auth, timeout=5)
            response.raise_for_status()
            data = response.json()
            return {
                'success': True,
                'message': 'Orthanc 연결 성공',
                'version': data.get('Version', 'Unknown'),
                'name': data.get('Name', 'Unknown')
            }
        except requests.RequestException as e:
            logger.error(f"Orthanc health check failed: {e}")
            return {'success': False, 'message': 'Orthanc 연결 실패', 'error': str(e)}
    
    def get_studies(self, limit=100, since=0):
        """모든 Study 목록 조회"""
        try:
            url = f"{self.base_url}/studies"
            params = {'limit': limit, 'since': since}
            response = requests.get(url, auth=self.auth, params=params, timeout=10)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            logger.error(f"Failed to get studies: {e}")
            return []
    
    def get_study(self, study_id):
        """Study 상세 정보 조회"""
        try:
            url = f"{self.base_url}/studies/{study_id}"
            response = requests.get(url, auth=self.auth, timeout=10)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            logger.error(f"Failed to get study {study_id}: {e}")
            raise
    
    def get_study_metadata(self, study_id):
        """Study의 DICOM 메타데이터 조회"""
        try:
            # Study의 첫 번째 Instance에서 메타데이터 추출
            study_data = self.get_study(study_id)
            if 'Instances' in study_data and len(study_data['Instances']) > 0:
                instance_id = study_data['Instances'][0]
                url = f"{self.base_url}/instances/{instance_id}/simplified-tags"
                response = requests.get(url, auth=self.auth, timeout=10)
                response.raise_for_status()
                return response.json()
            return {}
        except requests.RequestException as e:
            logger.error(f"Failed to get study metadata {study_id}: {e}")
            return {}
    
    def search_studies(self, patient_name=None, patient_id=None, study_date=None):
        """DICOM Query/Retrieve로 Study 검색"""
        try:
            url = f"{self.base_url}/tools/find"
            query = {"Level": "Study", "Query": {}, "Expand": True}
            
            if patient_name:
                query["Query"]["PatientName"] = f"*{patient_name}*"
            if patient_id:
                query["Query"]["PatientID"] = patient_id
            if study_date:
                query["Query"]["StudyDate"] = study_date
                
            response = requests.post(url, json=query, auth=self.auth, timeout=10)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            logger.error(f"Failed to search studies: {e}")
            return []
    
    def download_dicom_instance(self, instance_id):
        """DICOM 인스턴스 파일 다운로드"""
        try:
            url = f"{self.base_url}/instances/{instance_id}/file"
            response = requests.get(url, auth=self.auth, timeout=30)
            response.raise_for_status()
            return response.content
        except requests.RequestException as e:
            logger.error(f"Failed to download instance {instance_id}: {e}")
            raise
    
    def get_study_instances(self, study_id):
        """Study의 모든 Instance ID 목록"""
        try:
            study_data = self.get_study(study_id)
            return study_data.get('Instances', [])
        except Exception as e:
            logger.error(f"Failed to get instances for study {study_id}: {e}")
            return []

    def get_study_url_with_jwt(self, orthanc_id: str, study_instance_uid: str) -> dict:
        """
        Orthanc에서 JWT로 암호화된 Study URL 생성
        
        Args:
            orthanc_id: Orthanc 내부 Study ID (SHA-1)
            study_instance_uid: DICOM StudyInstanceUID
        """
        cache_key = f"orthanc_jwt_url:study:{study_instance_uid}"

        # Redis 캐시 확인
        cached_data = cache.get(cache_key)
        if cached_data:
            expires_at = datetime.fromisoformat(cached_data['expires_at'])
            if datetime.now() < (expires_at - timedelta(minutes=10)):
                cached_data['cached'] = True
                return cached_data

        # Orthanc에 JWT URL 요청
        try:
            # Orthanc API의 /studies/{id} 는 'Orthanc ID'를 사용해야 함
            response = requests.get(
                f"{self.base_url}/studies/{orthanc_id}",
                auth=self.auth,
                params={"jwt": "true"},
                timeout=5
            )
            
            # 404 등 에러 발생 시 fallback 처리 (크래시 방지)
            if response.status_code != 200:
                logger.warning(f"Orthanc /studies/{orthanc_id} returned {response.status_code}. Using fallback URL.")
                return {
                    'url': f"{self.base_url}/dicom-web/studies/{study_instance_uid}",
                    'token': None,
                    'expires_at': datetime.now().isoformat(),
                    'cached': False
                }

            orthanc_response = response.json()
            jwt_url_data = {
                'url': orthanc_response.get('url') or f"{self.base_url}/dicom-web/studies/{study_instance_uid}",
                'token': orthanc_response.get('token'),
                'expires_at': (datetime.now() + timedelta(hours=self.JWT_URL_LIFETIME_HOURS)).isoformat(),
                'cached': False
            }

            cache.set(cache_key, jwt_url_data, timeout=self.CACHE_TTL_SECONDS)
            return jwt_url_data

        except Exception as e:
            logger.error(f"Failed to generate JWT URL for {study_instance_uid}: {e}")
            return {
                'url': f"{self.base_url}/dicom-web/studies/{study_instance_uid}",
                'token': None,
                'expires_at': datetime.now().isoformat(),
                'cached': False,
                'error': str(e)
            }

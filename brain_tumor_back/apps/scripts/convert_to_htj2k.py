"""
DICOM을 HTJ2K 형식으로 변환

Orthanc의 /modify API를 사용하여 기존 DICOM을 HTJ2K로 변환합니다.
변환된 파일은 새로운 Study로 저장되며, 원본은 유지됩니다.
"""

import requests
import logging
import time
import json

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class HTJ2KConverter:
    """DICOM → HTJ2K 변환기"""

    HTJ2K_LOSSLESS = '1.2.840.10008.1.2.4.201'

    def __init__(self, orthanc_url='http://localhost:8042'):
        self.orthanc_url = orthanc_url
        self.session = requests.Session()
        self.stats = {
            'total_studies': 0,
            'success_studies': 0,
            'failed_studies': 0,
            'total_instances': 0
        }

    def get_patients(self):
        """환자 목록 조회"""
        try:
            response = self.session.get(f'{self.orthanc_url}/patients')
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"❌ 환자 목록 조회 실패: {e}")
            return []

    def get_patient_info(self, patient_id):
        """환자 상세 정보 조회"""
        try:
            response = self.session.get(f'{self.orthanc_url}/patients/{patient_id}')
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"❌ 환자 정보 조회 실패: {e}")
            return None

    def get_study_info(self, study_id):
        """Study 상세 정보 조회"""
        try:
            response = self.session.get(f'{self.orthanc_url}/studies/{study_id}')
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"❌ Study 정보 조회 실패: {e}")
            return None

    def convert_study_to_htj2k(self, study_id):
        """
        Study를 HTJ2K로 변환

        Orthanc의 /studies/{id}/modify API를 사용하여
        Transfer Syntax를 HTJ2K로 변환합니다.
        """
        try:
            # Study 정보 조회
            study_info = self.get_study_info(study_id)
            if not study_info:
                return False

            patient_id = study_info['ParentPatient']
            num_instances = len(study_info.get('Instances', []))

            tags = study_info.get('MainDicomTags', {})
            study_desc = tags.get('StudyDescription', 'Unknown')

            logger.info(f"\n   Study: {study_desc}")
            logger.info(f"   인스턴스: {num_instances}개")
            self.stats['total_instances'] += num_instances

            # HTJ2K로 변환 요청
            modify_payload = {
                "Transcode": self.HTJ2K_LOSSLESS,
                "Force": True,
                "Keep": ["StudyInstanceUID", "SeriesInstanceUID"],
                "KeepSource": True  # 원본 유지
            }

            logger.info(f"   🔄 HTJ2K 변환 시작...")
            response = self.session.post(
                f'{self.orthanc_url}/studies/{study_id}/modify',
                json=modify_payload,
                timeout=300  # 5분
            )

            if response.status_code == 200:
                result = response.json()
                new_study_id = result.get('ID')
                logger.info(f"   ✅ 변환 완료: {new_study_id[:16]}...")
                self.stats['success_studies'] += 1
                return True
            else:
                logger.error(f"   ❌ 변환 실패: HTTP {response.status_code}")
                logger.error(f"   응답: {response.text}")
                self.stats['failed_studies'] += 1
                return False

        except Exception as e:
            logger.error(f"❌ Study 변환 오류: {e}")
            self.stats['failed_studies'] += 1
            return False

    def convert_patient_studies(self, patient_filter=None, study_limit=None):
        """
        환자의 Study들을 HTJ2K로 변환

        Args:
            patient_filter: 특정 환자 ID (None이면 전체)
            study_limit: 변환할 Study 개수 제한
        """
        logger.info("=" * 80)
        logger.info("🔄 DICOM → HTJ2K 변환 시작")
        logger.info("=" * 80)

        # 1. 환자 목록 조회
        patients = self.get_patients()
        logger.info(f"📊 전체 환자 수: {len(patients)}명")

        if not patients:
            logger.warning("⚠️  환자 데이터가 없습니다.")
            return

        # 2. 환자별 처리
        for patient_orthanc_id in patients:
            patient_info = self.get_patient_info(patient_orthanc_id)
            if not patient_info:
                continue

            patient_id = patient_info['MainDicomTags'].get('PatientID', 'Unknown')

            # 환자 필터링
            if patient_filter and patient_id != patient_filter:
                continue

            studies = patient_info.get('Studies', [])
            logger.info(f"\n{'='*80}")
            logger.info(f"👤 환자: {patient_id}")
            logger.info(f"   Study 수: {len(studies)}개")
            logger.info(f"{'='*80}")

            # 3. Study별 변환
            processed_count = 0
            for idx, study_id in enumerate(studies, 1):
                if study_limit and processed_count >= study_limit:
                    logger.info(f"\n⏸️  Study 제한 도달 ({study_limit}개)")
                    break

                logger.info(f"\n[{idx}/{len(studies)}] Study ID: {study_id[:16]}...")
                self.stats['total_studies'] += 1

                success = self.convert_study_to_htj2k(study_id)
                if success:
                    processed_count += 1

                time.sleep(0.5)  # API 과부하 방지

        # 4. 통계 출력
        logger.info("\n" + "=" * 80)
        logger.info("📈 변환 완료 통계")
        logger.info("=" * 80)
        logger.info(f"총 Study: {self.stats['total_studies']}개")
        logger.info(f"✅ 성공: {self.stats['success_studies']}개")
        logger.info(f"❌ 실패: {self.stats['failed_studies']}개")
        logger.info(f"총 인스턴스: {self.stats['total_instances']:,}개")
        logger.info("=" * 80)

    def list_all_studies(self):
        """모든 Study 목록 출력 (Transfer Syntax 포함)"""
        logger.info("=" * 80)
        logger.info("📋 Orthanc 내 Study 목록")
        logger.info("=" * 80)

        patients = self.get_patients()

        for patient_orthanc_id in patients:
            patient_info = self.get_patient_info(patient_orthanc_id)
            if not patient_info:
                continue

            patient_id = patient_info['MainDicomTags'].get('PatientID', 'Unknown')
            studies = patient_info.get('Studies', [])

            logger.info(f"\n👤 환자: {patient_id}")
            logger.info(f"   Study 수: {len(studies)}개")

            for study_id in studies:
                study_info = self.get_study_info(study_id)
                if not study_info:
                    continue

                tags = study_info.get('MainDicomTags', {})
                study_desc = tags.get('StudyDescription', 'Unknown')
                num_instances = len(study_info.get('Instances', []))

                # 첫 번째 인스턴스의 Transfer Syntax 확인
                instances = study_info.get('Instances', [])
                transfer_syntax = "Unknown"
                if instances:
                    try:
                        inst_response = self.session.get(
                            f'{self.orthanc_url}/instances/{instances[0]}/tags?simplify'
                        )
                        if inst_response.status_code == 200:
                            inst_tags = inst_response.json()
                            transfer_syntax = inst_tags.get('TransferSyntaxUID', 'Unknown')
                    except:
                        pass

                is_htj2k = "✅ HTJ2K" if transfer_syntax == self.HTJ2K_LOSSLESS else "📦 기본"

                logger.info(f"   - {study_desc}")
                logger.info(f"     ID: {study_id[:16]}... | {num_instances}개 | {is_htj2k}")
                logger.info(f"     Transfer Syntax: {transfer_syntax}")


def main():
    """메인 실행 함수"""

    ORTHANC_URL = 'http://localhost:8042'

    # 옵션 1: 모든 Study 목록 보기 (변환 전 확인용)
    # COMMAND = 'list'

    # 옵션 2: HTJ2K 변환
    COMMAND = 'convert'
    PATIENT_FILTER = None  # None: 전체, 'sub-0004': 특정 환자만
    STUDY_LIMIT = 1  # 테스트용: 각 환자당 1개 Study만 변환

    converter = HTJ2KConverter(orthanc_url=ORTHANC_URL)

    if COMMAND == 'list':
        converter.list_all_studies()

    elif COMMAND == 'convert':
        logger.info("\n⚙️  변환 설정")
        logger.info(f"   Orthanc URL: {ORTHANC_URL}")
        logger.info(f"   환자 필터: {PATIENT_FILTER or '전체'}")
        logger.info(f"   Study 제한: {STUDY_LIMIT}개")
        logger.info("")

        converter.convert_patient_studies(
            patient_filter=PATIENT_FILTER,
            study_limit=STUDY_LIMIT
        )

        logger.info(f"\n✅ 변환 작업이 완료되었습니다!")
        logger.info(f"Orthanc 웹 UI: {ORTHANC_URL}/app/explorer.html")


if __name__ == '__main__':
    main()

"""
기존 DICOM을 다운로드 후 재업로드하여 HTJ2K로 변환

Orthanc의 IngestTranscoding 설정(HTJ2K)을 활용하여
기존 DICOM을 다운로드 → 삭제 → 재업로드하면 자동으로 HTJ2K로 변환됩니다.
"""

import requests
import logging
import time
import tempfile
from pathlib import Path

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class OrthancReloader:
    """Orthanc DICOM 재로드 (HTJ2K 변환)"""

    HTJ2K_LOSSLESS = '1.2.840.10008.1.2.4.201'

    def __init__(self, orthanc_url='http://localhost:8042'):
        self.orthanc_url = orthanc_url
        self.session = requests.Session()
        self.stats = {
            'total_studies': 0,
            'success': 0,
            'failed': 0,
            'total_instances': 0
        }

    def get_patients(self):
        """환자 목록 조회"""
        response = self.session.get(f'{self.orthanc_url}/patients')
        response.raise_for_status()
        return response.json()

    def get_patient_info(self, patient_id):
        """환자 상세 정보"""
        response = self.session.get(f'{self.orthanc_url}/patients/{patient_id}')
        response.raise_for_status()
        return response.json()

    def get_study_info(self, study_id):
        """Study 상세 정보"""
        response = self.session.get(f'{self.orthanc_url}/studies/{study_id}')
        response.raise_for_status()
        return response.json()

    def check_instance_transfer_syntax(self, instance_id):
        """인스턴스의 Transfer Syntax 확인"""
        response = self.session.get(
            f'{self.orthanc_url}/instances/{instance_id}/tags?simplify'
        )
        if response.status_code == 200:
            tags = response.json()
            return tags.get('TransferSyntaxUID', 'Unknown')
        return 'Unknown'

    def reload_study_as_htj2k(self, study_id, patient_id):
        """
        Study를 다운로드 후 재업로드하여 HTJ2K로 변환
        """
        try:
            study_info = self.get_study_info(study_id)
            instances = study_info.get('Instances', [])
            num_instances = len(instances)

            tags = study_info.get('MainDicomTags', {})
            study_desc = tags.get('StudyDescription', 'Unknown')

            logger.info(f"\n   Study: {study_desc}")
            logger.info(f"   인스턴스: {num_instances}개")

            # 첫 번째 인스턴스의 Transfer Syntax 확인
            if instances:
                current_syntax = self.check_instance_transfer_syntax(instances[0])
                logger.info(f"   현재 Transfer Syntax: {current_syntax}")

                if current_syntax == self.HTJ2K_LOSSLESS:
                    logger.info(f"   ⏭️  이미 HTJ2K 형식")
                    self.stats['total_instances'] += num_instances
                    return True

            # 1. 모든 인스턴스 다운로드
            logger.info(f"   📥 {num_instances}개 인스턴스 다운로드 중...")
            downloaded_files = []

            for idx, instance_id in enumerate(instances):
                response = self.session.get(f'{self.orthanc_url}/instances/{instance_id}/file')
                if response.status_code == 200:
                    temp_file = tempfile.NamedTemporaryFile(suffix='.dcm', delete=False)
                    temp_file.write(response.content)
                    temp_file.close()
                    downloaded_files.append(temp_file.name)

                if (idx + 1) % 50 == 0:
                    logger.info(f"      진행: {idx+1}/{num_instances}")

            logger.info(f"   ✅ 다운로드 완료: {len(downloaded_files)}개")

            # 2. Study 삭제
            logger.info(f"   🗑️  기존 Study 삭제 중...")
            del_response = self.session.delete(f'{self.orthanc_url}/studies/{study_id}')

            if del_response.status_code not in [200, 204]:
                logger.error(f"   ❌ Study 삭제 실패: HTTP {del_response.status_code}")
                # 파일 정리
                for file_path in downloaded_files:
                    Path(file_path).unlink()
                return False

            time.sleep(1)  # 삭제 완료 대기

            # 3. 재업로드 (HTJ2K로 자동 변환됨)
            logger.info(f"   📤 HTJ2K로 재업로드 중...")
            uploaded_count = 0

            for idx, file_path in enumerate(downloaded_files):
                with open(file_path, 'rb') as f:
                    dicom_data = f.read()

                upload_response = self.session.post(
                    f'{self.orthanc_url}/instances',
                    data=dicom_data,
                    headers={'Content-Type': 'application/dicom'}
                )

                if upload_response.status_code in [200, 201]:
                    uploaded_count += 1
                else:
                    logger.warning(f"      ⚠️  업로드 실패: 인스턴스 {idx+1}")

                # 파일 삭제
                Path(file_path).unlink()

                if (idx + 1) % 50 == 0:
                    logger.info(f"      진행: {idx+1}/{len(downloaded_files)}")

            logger.info(f"   ✅ 재업로드 완료: {uploaded_count}/{len(downloaded_files)}개")

            # 4. 변환 확인
            time.sleep(1)
            patients = self.get_patients()
            for patient_orthanc_id in patients:
                patient_info = self.get_patient_info(patient_orthanc_id)
                if patient_info['MainDicomTags'].get('PatientID') == patient_id:
                    studies = patient_info.get('Studies', [])
                    for new_study_id in studies:
                        new_study_info = self.get_study_info(new_study_id)
                        new_instances = new_study_info.get('Instances', [])
                        if new_instances:
                            new_syntax = self.check_instance_transfer_syntax(new_instances[0])
                            logger.info(f"   🔍 새 Transfer Syntax: {new_syntax}")

                            if new_syntax == self.HTJ2K_LOSSLESS:
                                logger.info(f"   ✅ HTJ2K 변환 성공!")
                                self.stats['success'] += 1
                                self.stats['total_instances'] += uploaded_count
                                return True
                            else:
                                logger.warning(f"   ⚠️  HTJ2K 변환 실패 (여전히 {new_syntax})")

            return False

        except Exception as e:
            logger.error(f"❌ Study 재로드 오류: {e}")
            self.stats['failed'] += 1
            return False

    def reload_patient_studies(self, patient_filter=None, study_limit=1):
        """환자의 Study들을 재로드"""
        logger.info("=" * 80)
        logger.info("🔄 DICOM → HTJ2K 재로드 시작")
        logger.info("=" * 80)

        patients = self.get_patients()
        logger.info(f"📊 전체 환자 수: {len(patients)}명")

        for patient_orthanc_id in patients:
            patient_info = self.get_patient_info(patient_orthanc_id)
            patient_id = patient_info['MainDicomTags'].get('PatientID', 'Unknown')

            if patient_filter and patient_id != patient_filter:
                continue

            studies = patient_info.get('Studies', [])
            logger.info(f"\n{'='*80}")
            logger.info(f"👤 환자: {patient_id}")
            logger.info(f"   Study 수: {len(studies)}개")
            logger.info(f"{'='*80}")

            processed_count = 0
            for idx, study_id in enumerate(studies, 1):
                if study_limit and processed_count >= study_limit:
                    logger.info(f"\n⏸️  Study 제한 도달 ({study_limit}개)")
                    break

                logger.info(f"\n[{idx}/{len(studies)}] Study ID: {study_id[:16]}...")
                self.stats['total_studies'] += 1

                success = self.reload_study_as_htj2k(study_id, patient_id)
                if success:
                    processed_count += 1

                time.sleep(1)

        # 통계 출력
        logger.info("\n" + "=" * 80)
        logger.info("📈 재로드 완료 통계")
        logger.info("=" * 80)
        logger.info(f"총 Study: {self.stats['total_studies']}개")
        logger.info(f"✅ 성공: {self.stats['success']}개")
        logger.info(f"❌ 실패: {self.stats['failed']}개")
        logger.info(f"총 인스턴스: {self.stats['total_instances']:,}개")
        logger.info("=" * 80)


def main():
    ORTHANC_URL = 'http://localhost:8042'
    PATIENT_FILTER = 'sub-0004'  # 테스트: sub-0004 환자만
    STUDY_LIMIT = 1  # 테스트: 1개 Study만

    reloader = OrthancReloader(orthanc_url=ORTHANC_URL)

    logger.info("\n⚙️  재로드 설정")
    logger.info(f"   Orthanc URL: {ORTHANC_URL}")
    logger.info(f"   환자 필터: {PATIENT_FILTER or '전체'}")
    logger.info(f"   Study 제한: {STUDY_LIMIT}개")
    logger.info("")

    reloader.reload_patient_studies(
        patient_filter=PATIENT_FILTER,
        study_limit=STUDY_LIMIT
    )

    logger.info(f"\n✅ 재로드 작업이 완료되었습니다!")
    logger.info(f"Orthanc 웹 UI: {ORTHANC_URL}/app/explorer.html")


if __name__ == '__main__':
    main()

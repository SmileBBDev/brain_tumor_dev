"""
DICOM 파일 Orthanc 업로드 스크립트

로컬에 저장된 DICOM 파일들을 Orthanc PACS 서버로 업로드합니다.
"""

import os
import requests
from pathlib import Path
import logging

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class OrthancUploader:
    """Orthanc PACS 서버로 DICOM 파일 업로드"""

    def __init__(self, orthanc_url='http://localhost:8042'):
        self.orthanc_url = orthanc_url
        self.auth = None
        self.upload_endpoint = f'{orthanc_url}/instances'

        # 통계
        self.total_files = 0
        self.success_count = 0
        self.fail_count = 0
        self.failed_files = []

    def check_orthanc_connection(self):
        """Orthanc 서버 연결 확인"""
        try:
            response = requests.get(
                f'{self.orthanc_url}/system',
                auth=self.auth,
                timeout=5
            )
            if response.status_code == 200:
                system_info = response.json()
                logger.info(f"✅ Orthanc 서버 연결 성공!")
                logger.info(f"   버전: {system_info.get('Version', 'Unknown')}")
                logger.info(f"   이름: {system_info.get('Name', 'Unknown')}")
                return True
            else:
                logger.error(f"❌ Orthanc 서버 응답 오류: {response.status_code}")
                return False
        except requests.exceptions.RequestException as e:
            logger.error(f"❌ Orthanc 서버 연결 실패: {str(e)}")
            logger.error(f"   URL: {self.orthanc_url}")
            logger.error(f"   Orthanc 서버가 실행 중인지 확인해주세요.")
            return False

    def upload_dicom_file(self, file_path):
        """단일 DICOM 파일 업로드"""
        try:
            with open(file_path, 'rb') as f:
                dicom_data = f.read()

            response = requests.post(
                self.upload_endpoint,
                data=dicom_data,
                auth=self.auth,
                headers={'Content-Type': 'application/dicom'},
                timeout=30
            )

            if response.status_code in [200, 201]:
                result = response.json()
                instance_id = result.get('ID', 'Unknown')
                logger.info(f"✅ 업로드 성공: {file_path.name} (Instance ID: {instance_id})")
                self.success_count += 1
                return True
            else:
                logger.warning(f"⚠️  업로드 실패: {file_path.name} (Status: {response.status_code})")
                self.fail_count += 1
                self.failed_files.append(str(file_path))
                return False

        except Exception as e:
            logger.error(f"❌ 파일 업로드 오류: {file_path.name} - {str(e)}")
            self.fail_count += 1
            self.failed_files.append(str(file_path))
            return False

    def find_dicom_files(self, directory):
        """디렉토리에서 모든 DICOM 파일 찾기 (재귀)"""
        dicom_files = []
        directory_path = Path(directory)

        if not directory_path.exists():
            logger.error(f"❌ 디렉토리가 존재하지 않습니다: {directory}")
            return dicom_files

        logger.info(f"📁 디렉토리 스캔 중: {directory}")

        # .dcm 파일과 확장자 없는 DICOM 파일 모두 찾기
        for file_path in directory_path.rglob('*'):
            if file_path.is_file():
                # .dcm 확장자 또는 확장자 없는 파일 (DICOM은 확장자 없을 수 있음)
                if file_path.suffix.lower() == '.dcm' or file_path.suffix == '':
                    # 파일 크기가 너무 작으면 제외 (메타데이터 파일 등)
                    if file_path.stat().st_size > 128:  # 최소 128 바이트
                        dicom_files.append(file_path)

        logger.info(f"   발견된 DICOM 파일: {len(dicom_files)}개")
        return dicom_files

    def upload_directory(self, directory):
        """디렉토리 내 모든 DICOM 파일 업로드"""
        dicom_files = self.find_dicom_files(directory)

        if not dicom_files:
            logger.warning(f"⚠️  DICOM 파일을 찾을 수 없습니다: {directory}")
            return

        logger.info(f"\n📤 업로드 시작: {len(dicom_files)}개 파일")
        logger.info("-" * 80)

        for i, file_path in enumerate(dicom_files, 1):
            logger.info(f"[{i}/{len(dicom_files)}] 처리 중...")
            self.upload_dicom_file(file_path)
            self.total_files += 1

        logger.info("-" * 80)

    def print_summary(self):
        """업로드 결과 요약 출력"""
        logger.info("\n" + "=" * 80)
        logger.info("📊 업로드 완료 - 결과 요약")
        logger.info("=" * 80)
        logger.info(f"총 파일 수:    {self.total_files}개")
        logger.info(f"성공:          {self.success_count}개 ✅")
        logger.info(f"실패:          {self.fail_count}개 ❌")
        logger.info(f"성공률:        {(self.success_count/self.total_files*100) if self.total_files > 0 else 0:.1f}%")

        if self.failed_files:
            logger.info("\n⚠️  실패한 파일 목록:")
            for failed_file in self.failed_files:
                logger.info(f"   - {failed_file}")

        logger.info("=" * 80)


def main():
    """메인 실행 함수"""

    # Orthanc 서버 설정
    ORTHANC_URL = 'http://localhost:8042'

    # 업로드할 환자 데이터 경로
    PATIENT_DIRECTORIES = [
        r'C:\Users\302-28\Downloads\sub\sub-0004',
        r'C:\Users\302-28\Downloads\sub\sub-0005',
    ]

    logger.info("=" * 80)
    logger.info("🏥 DICOM 파일 Orthanc 업로드 시작")
    logger.info("=" * 80)
    logger.info(f"Orthanc 서버: {ORTHANC_URL}")
    logger.info(f"대상 환자 수: {len(PATIENT_DIRECTORIES)}명")
    logger.info("")

    # Uploader 인스턴스 생성
    uploader = OrthancUploader(orthanc_url=ORTHANC_URL)

    # Orthanc 서버 연결 확인
    if not uploader.check_orthanc_connection():
        logger.error("\n❌ Orthanc 서버에 연결할 수 없습니다. 스크립트를 종료합니다.")
        logger.error("다음을 확인해주세요:")
        logger.error("  1. Orthanc 서버가 실행 중인가? (docker-compose up -d)")
        logger.error("  2. URL이 올바른가? (기본: http://localhost:8042)")
        return

    logger.info("")

    # 각 환자 디렉토리 업로드
    for i, patient_dir in enumerate(PATIENT_DIRECTORIES, 1):
        logger.info(f"\n{'='*80}")
        logger.info(f"👤 환자 {i}/{len(PATIENT_DIRECTORIES)} 처리 중")
        logger.info(f"{'='*80}")
        uploader.upload_directory(patient_dir)

    # 결과 요약 출력
    uploader.print_summary()

    # Orthanc에 업로드된 환자 수 확인
    try:
        response = requests.get(
            f'{ORTHANC_URL}/patients',
            timeout=5
        )
        if response.status_code == 200:
            patients = response.json()
            logger.info(f"\n✅ Orthanc에 저장된 총 환자 수: {len(patients)}명")
            logger.info(f"   환자 ID 목록: {patients[:5]}{'...' if len(patients) > 5 else ''}")
    except Exception as e:
        logger.warning(f"⚠️  환자 수 확인 실패: {str(e)}")

    logger.info("\n🎉 모든 작업이 완료되었습니다!")
    logger.info(f"Orthanc 웹 UI: {ORTHANC_URL}/app/explorer.html")
    logger.info("")


if __name__ == '__main__':
    main()

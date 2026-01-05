"""
NIfTI 파일을 DICOM으로 변환하여 Orthanc에 업로드

NIfTI (.nii.gz) 파일을 DICOM 형식으로 변환합니다.
"""

import os
import nibabel as nib
import numpy as np
import pydicom
from pydicom.dataset import Dataset, FileDataset
from datetime import datetime
import requests
from pathlib import Path
import logging

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class NIfTIToDICOMConverter:
    """NIfTI 파일을 DICOM으로 변환"""

    def __init__(self, orthanc_url='http://localhost:8042'):
        self.orthanc_url = orthanc_url
        self.upload_endpoint = f'{orthanc_url}/instances'

        # 통계
        self.total_files = 0
        self.success_count = 0
        self.fail_count = 0

    def create_dicom_from_nifti(self, nifti_path, patient_id, study_id, series_number, modality='MR'):
        """
        NIfTI 파일에서 DICOM 시리즈 생성

        Args:
            nifti_path: NIfTI 파일 경로
            patient_id: 환자 ID
            study_id: Study UID
            series_number: 시리즈 번호
            modality: 영상 모달리티 (기본: MR)

        Returns:
            list: DICOM 파일 경로 리스트
        """
        try:
            # NIfTI 파일 로드
            logger.info(f"📖 NIfTI 파일 로드 중: {Path(nifti_path).name}")
            nii_img = nib.load(nifti_path)
            img_data = nii_img.get_fdata()

            # 파일명에서 시리즈 설명 추출
            file_name = Path(nifti_path).stem.replace('.nii', '')
            series_description = file_name.split('_')[-1] if '_' in file_name else file_name

            logger.info(f"   이미지 크기: {img_data.shape}")
            logger.info(f"   시리즈 설명: {series_description}")

            # DICOM 파일 리스트
            dicom_files = []

            # 3D 볼륨을 슬라이스로 분할
            if len(img_data.shape) == 3:
                num_slices = img_data.shape[2]
            elif len(img_data.shape) == 4:
                # 4D 데이터인 경우 첫 번째 볼륨만 사용
                img_data = img_data[:, :, :, 0]
                num_slices = img_data.shape[2]
            else:
                logger.warning(f"⚠️  지원하지 않는 이미지 차원: {img_data.shape}")
                return []

            logger.info(f"   총 슬라이스 수: {num_slices}")

            # 임시 디렉토리 생성
            temp_dir = Path(f"temp_dicom/{patient_id}/{series_number}")
            temp_dir.mkdir(parents=True, exist_ok=True)

            # 각 슬라이스를 DICOM으로 변환
            for slice_idx in range(num_slices):
                slice_data = img_data[:, :, slice_idx]

                # DICOM 파일 생성
                dicom_path = temp_dir / f"slice_{slice_idx:04d}.dcm"
                self._create_dicom_slice(
                    slice_data,
                    dicom_path,
                    patient_id,
                    study_id,
                    series_number,
                    slice_idx,
                    num_slices,
                    series_description,
                    modality
                )
                dicom_files.append(dicom_path)

            logger.info(f"✅ DICOM 변환 완료: {len(dicom_files)}개 슬라이스")
            return dicom_files

        except Exception as e:
            logger.error(f"❌ NIfTI → DICOM 변환 실패: {str(e)}")
            return []

    def _create_dicom_slice(self, slice_data, output_path, patient_id, study_uid,
                           series_number, instance_number, total_slices,
                           series_description, modality):
        """단일 DICOM 슬라이스 생성"""

        # 데이터 정규화 (0-4095 범위로)
        slice_data = slice_data.astype(np.float64)
        slice_min = slice_data.min()
        slice_max = slice_data.max()

        if slice_max > slice_min:
            slice_data = ((slice_data - slice_min) / (slice_max - slice_min) * 4095)

        slice_data = slice_data.astype(np.uint16)

        # 파일 메타 정보
        file_meta = Dataset()
        file_meta.MediaStorageSOPClassUID = '1.2.840.10008.5.1.4.1.1.4'  # MR Image Storage
        file_meta.MediaStorageSOPInstanceUID = pydicom.uid.generate_uid()
        file_meta.TransferSyntaxUID = pydicom.uid.ExplicitVRLittleEndian
        file_meta.ImplementationClassUID = pydicom.uid.generate_uid()

        # DICOM 데이터셋 생성
        ds = FileDataset(str(output_path), {}, file_meta=file_meta, preamble=b"\0" * 128)

        # 환자 정보
        ds.PatientName = f"Patient_{patient_id}"
        ds.PatientID = patient_id
        ds.PatientBirthDate = '19800101'
        ds.PatientSex = 'O'

        # Study 정보
        ds.StudyInstanceUID = study_uid
        ds.StudyID = patient_id
        ds.StudyDate = datetime.now().strftime('%Y%m%d')
        ds.StudyTime = datetime.now().strftime('%H%M%S')
        ds.StudyDescription = f'Brain MRI - {patient_id}'

        # Series 정보
        ds.SeriesInstanceUID = pydicom.uid.generate_uid()
        ds.SeriesNumber = series_number
        ds.SeriesDescription = series_description
        ds.Modality = modality

        # Instance 정보
        ds.SOPInstanceUID = file_meta.MediaStorageSOPInstanceUID
        ds.SOPClassUID = file_meta.MediaStorageSOPClassUID
        ds.InstanceNumber = instance_number + 1

        # 이미지 정보
        ds.SamplesPerPixel = 1
        ds.PhotometricInterpretation = "MONOCHROME2"
        ds.Rows = slice_data.shape[0]
        ds.Columns = slice_data.shape[1]
        ds.BitsAllocated = 16
        ds.BitsStored = 12
        ds.HighBit = 11
        ds.PixelRepresentation = 0

        # 이미지 위치 정보
        ds.ImagePositionPatient = [0, 0, instance_number * 1.0]
        ds.ImageOrientationPatient = [1, 0, 0, 0, 1, 0]
        ds.SliceThickness = 1.0
        ds.PixelSpacing = [1.0, 1.0]
        ds.SliceLocation = instance_number * 1.0

        # 픽셀 데이터
        ds.PixelData = slice_data.tobytes()

        # 파일 저장
        ds.save_as(output_path, write_like_original=False)

    def upload_dicom_to_orthanc(self, dicom_path):
        """DICOM 파일을 Orthanc에 업로드"""
        try:
            with open(dicom_path, 'rb') as f:
                dicom_data = f.read()

            response = requests.post(
                self.upload_endpoint,
                data=dicom_data,
                headers={'Content-Type': 'application/dicom'},
                timeout=30
            )

            if response.status_code in [200, 201]:
                self.success_count += 1
                return True
            else:
                self.fail_count += 1
                return False

        except Exception as e:
            logger.error(f"❌ 업로드 실패: {dicom_path.name} - {str(e)}")
            self.fail_count += 1
            return False

    def process_nifti_file(self, nifti_path, patient_id, series_number):
        """NIfTI 파일 처리 (변환 → 업로드)"""
        logger.info(f"\n{'='*80}")
        logger.info(f"📄 처리 중: {Path(nifti_path).name}")
        logger.info(f"{'='*80}")

        # Study UID 생성
        study_uid = pydicom.uid.generate_uid()

        # NIfTI → DICOM 변환
        dicom_files = self.create_dicom_from_nifti(
            nifti_path,
            patient_id,
            study_uid,
            series_number
        )

        if not dicom_files:
            logger.warning(f"⚠️  변환된 DICOM 파일이 없습니다.")
            return

        # Orthanc에 업로드
        logger.info(f"\n📤 Orthanc 업로드 시작...")
        for i, dicom_file in enumerate(dicom_files):
            if (i + 1) % 10 == 0:
                logger.info(f"   진행: {i+1}/{len(dicom_files)}")
            self.upload_dicom_to_orthanc(dicom_file)

        logger.info(f"✅ 업로드 완료: {self.success_count}개 성공, {self.fail_count}개 실패")

        # 임시 파일 정리
        import shutil
        temp_dir = Path(f"temp_dicom/{patient_id}/{series_number}")
        if temp_dir.exists():
            shutil.rmtree(temp_dir.parent.parent if temp_dir.parent.parent.name == "temp_dicom" else temp_dir)


def main():
    """메인 실행 함수"""

    ORTHANC_URL = 'http://localhost:8042'

    # 환자 디렉토리 자동 스캔
    PATIENT_DIRS = [
        r'C:\Users\302-28\Downloads\sub\sub-0004',
        r'C:\Users\302-28\Downloads\sub\sub-0005',
    ]

    NIFTI_FILES = []

    for patient_dir in PATIENT_DIRS:
        patient_path = Path(patient_dir)
        if not patient_path.exists():
            logger.warning(f"⚠️  디렉토리를 찾을 수 없습니다: {patient_dir}")
            continue

        patient_id = patient_path.name  # sub-0004, sub-0005
        series_num = 1

        # 모든 .nii.gz 파일 찾기
        for nii_file in sorted(patient_path.glob('*.nii.gz')):
            NIFTI_FILES.append({
                'path': str(nii_file),
                'patient_id': patient_id,
                'series_number': series_num
            })
            series_num += 1
            logger.info(f"📋 변환 대상 추가: {nii_file.name} (환자: {patient_id}, 시리즈: {series_num-1})")

    if not NIFTI_FILES:
        logger.error("❌ 변환할 NIfTI 파일을 찾을 수 없습니다.")
        return

    logger.info("="* 80)
    logger.info("🏥 NIfTI → DICOM 변환 및 Orthanc 업로드 시작")
    logger.info("=" * 80)
    logger.info(f"Orthanc 서버: {ORTHANC_URL}")
    logger.info(f"변환할 파일 수: {len(NIFTI_FILES)}개")
    logger.info("")

    converter = NIfTIToDICOMConverter(orthanc_url=ORTHANC_URL)

    for i, file_info in enumerate(NIFTI_FILES, 1):
        logger.info(f"\n{'#'*80}")
        logger.info(f"파일 {i}/{len(NIFTI_FILES)}")
        logger.info(f"{'#'*80}")

        if not Path(file_info['path']).exists():
            logger.warning(f"⚠️  파일을 찾을 수 없습니다: {file_info['path']}")
            continue

        converter.process_nifti_file(
            file_info['path'],
            file_info['patient_id'],
            file_info['series_number']
        )

    logger.info("\n" + "=" * 80)
    logger.info("🎉 모든 작업이 완료되었습니다!")
    logger.info("=" * 80)
    logger.info(f"Orthanc 웹 UI: {ORTHANC_URL}/app/explorer.html")
    logger.info("")


if __name__ == '__main__':
    main()

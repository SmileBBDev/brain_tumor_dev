"""
NIfTI (.nii.gz) 파일을 DICOM으로 변환하여 Orthanc에 업로드하는 스크립트.

주요 개선사항:
1. StudyInstanceUID 통일: 환자 단위로 하나의 Study UID를 공유하여 여러 시리즈가 하나의 검사로 묶이도록 함.
2. Orthanc 시각화 개선: WindowCenter, WindowWidth, Rescale 등의 태그를 명시적으로 설정하여 검은 화면 문제 해결.
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
import shutil

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

    def create_dicom_from_nifti(self, nifti_path, patient_id, study_uid, series_number, modality='MR'):
        """
        NIfTI 파일에서 DICOM 시리즈 생성
        """
        try:
            # NIfTI 파일 로드
            logger.info(f"📖 NIfTI 파일 로드 중: {Path(nifti_path).name}")
            nii_img = nib.load(nifti_path)
            img_data = nii_img.get_fdata()

            # 파일명에서 시리즈 설명 추출
            file_name = Path(nifti_path).stem.replace('.nii', '')
            # 예: Sub-0004_T1w -> T1w
            series_description = file_name.split('_')[-1] if '_' in file_name else file_name

            logger.info(f"   이미지 크기: {img_data.shape}")
            logger.info(f"   시리즈 설명: {series_description}")

            # DICOM 파일 리스트
            dicom_files = []

            # 3D 볼륨 처리
            if len(img_data.shape) == 3:
                num_slices = img_data.shape[2]
            elif len(img_data.shape) == 4:
                img_data = img_data[:, :, :, 0] # 첫 번째 볼륨만 사용
                num_slices = img_data.shape[2]
            else:
                logger.warning(f"⚠️  지원하지 않는 이미지 차원: {img_data.shape}")
                return []

            logger.info(f"   총 슬라이스 수: {num_slices}")

            # 임시 디렉토리 생성
            temp_dir = Path(f"temp_dicom/{patient_id}/{series_number}")
            if temp_dir.exists():
                shutil.rmtree(temp_dir)
            temp_dir.mkdir(parents=True, exist_ok=True)

            # SeriesInstanceUID 생성 (시리즈마다 고유)
            series_uid = pydicom.uid.generate_uid()
            # FrameOfReferenceUID 생성 (동일 좌표계 공유 시 동일하게 설정 가능하나, 여기선 시리즈 단위로 생성)
            frame_of_reference_uid = pydicom.uid.generate_uid()

            # 각 슬라이스를 DICOM으로 변환
            for slice_idx in range(num_slices):
                slice_data = img_data[:, :, slice_idx]

                # DICOM 파일 생성
                dicom_path = temp_dir / f"slice_{slice_idx:04d}.dcm"
                
                # 정규화 및 Windowing 정보 계산
                # 12비트(0~4095)로 정규화
                processed_data, window_center, window_width = self._normalize_slice(slice_data)
                
                self._create_dicom_slice(
                    processed_data,
                    dicom_path,
                    patient_id,
                    study_uid,
                    series_uid,
                    frame_of_reference_uid,
                    series_number,
                    slice_idx,
                    series_description,
                    modality,
                    window_center,
                    window_width
                )
                dicom_files.append(dicom_path)

            logger.info(f"✅ DICOM 변환 완료: {len(dicom_files)}개 슬라이스")
            return dicom_files

        except Exception as e:
            logger.error(f"❌ NIfTI → DICOM 변환 실패: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
            return []

    def _normalize_slice(self, slice_data):
        """데이터를 0-4095 범위로 정규화하고 Window 값 반환"""
        slice_data = slice_data.astype(np.float64)
        min_val = slice_data.min()
        max_val = slice_data.max()
        
        # 만약 데이터가 모두 0이거나 평탄하면 그대로 반환
        if max_val <= min_val:
            return np.zeros_like(slice_data, dtype=np.uint16), 2048, 4096

        # 0 ~ 4095 로 스케일링
        scaled_data = ((slice_data - min_val) / (max_val - min_val) * 4095)
        scaled_data = scaled_data.astype(np.uint16)
        
        # Window Center/Width 설정 (전체 범위를 잘 보여주도록)
        # Center: 중간값 (2048), Width: 전체 폭 (4096)
        # Orthanc 등 뷰어에서 기본적으로 이 값을 사용하여 렌더링함
        return scaled_data, 2048, 4096

    def _create_dicom_slice(self, slice_data, output_path, patient_id, study_uid,
                           series_uid, frame_of_reference_uid, series_number, instance_number,
                           series_description, modality, window_center, window_width):
        """단일 DICOM 슬라이스 생성 및 태그 설정"""

        # 파일 메타 정보
        file_meta = Dataset()
        file_meta.MediaStorageSOPClassUID = '1.2.840.10008.5.1.4.1.1.4'  # MR Image Storage
        file_meta.MediaStorageSOPInstanceUID = pydicom.uid.generate_uid()
        file_meta.TransferSyntaxUID = pydicom.uid.ExplicitVRLittleEndian
        file_meta.ImplementationClassUID = pydicom.uid.generate_uid()

        # DICOM 데이터셋 생성
        ds = FileDataset(str(output_path), {}, file_meta=file_meta, preamble=b"\0" * 128)

        # 필수: Patient 정보
        ds.PatientName = f"{patient_id}"
        ds.PatientID = patient_id
        ds.PatientBirthDate = '19800101' # 임의 날짜
        ds.PatientSex = 'O'

        # 필수: Study 정보 (중요: 외부에서 주입받은 동일한 UID 사용)
        ds.StudyInstanceUID = study_uid
        ds.StudyID = patient_id # Study ID는 사람이 읽기 쉬운 식별자
        ds.StudyDate = datetime.now().strftime('%Y%m%d')
        ds.StudyTime = datetime.now().strftime('%H%M%S')
        ds.AccessionNumber = ''
        ds.StudyDescription = f'Brain MRI - {patient_id}'

        # 필수: Series 정보
        ds.SeriesInstanceUID = series_uid
        ds.SeriesNumber = series_number
        ds.SeriesDescription = series_description
        ds.Modality = modality
        ds.FrameOfReferenceUID = frame_of_reference_uid

        # 필수: Instance 정보
        ds.SOPInstanceUID = file_meta.MediaStorageSOPInstanceUID
        ds.SOPClassUID = file_meta.MediaStorageSOPClassUID
        ds.InstanceNumber = instance_number + 1

        # 필수: 이미지 픽셀 구조 정보
        ds.SamplesPerPixel = 1
        ds.PhotometricInterpretation = "MONOCHROME2" # 0=Black, Max=White
        ds.Rows = slice_data.shape[0]
        ds.Columns = slice_data.shape[1]
        ds.BitsAllocated = 16
        ds.BitsStored = 12
        ds.HighBit = 11
        ds.PixelRepresentation = 0 # unsigned integer

        # 시각화 핵심 태그 (Windowing)
        ds.WindowCenter = window_center
        ds.WindowWidth = window_width
        ds.RescaleIntercept = "0"
        ds.RescaleSlope = "1"
        ds.RescaleType = "US" # Unspecified

        # 공간 및 위치 정보 (Slice 순서에 영향)
        ds.ImagePositionPatient = [0.0, 0.0, float(instance_number)]
        ds.ImageOrientationPatient = [1.0, 0.0, 0.0, 0.0, 1.0, 0.0] # Identity orientation
        ds.SliceThickness = 1.0
        ds.PixelSpacing = [1.0, 1.0]
        ds.SliceLocation = float(instance_number)
        
        # Laterality (빈 값이라도 넣어주는 게 좋음)
        ds.Laterality = '' 

        # 픽셀 데이터 저장
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
                logger.error(f"   Orthanc 응답 오류: {response.status_code} - {response.text}")
                self.fail_count += 1
                return False

        except Exception as e:
            logger.error(f"❌ 업로드 실패: {dicom_path.name} - {str(e)}")
            self.fail_count += 1
            return False

    def process_patient(self, patient_dir):
        """환자 단위 처리 (Study UID 통일)"""
        patient_path = Path(patient_dir)
        if not patient_path.exists():
            logger.warning(f"⚠️  디렉토리를 찾을 수 없습니다: {patient_dir}")
            return

        patient_id = patient_path.name
        logger.info(f"\n========================================")
        logger.info(f"🏥 환자 처리 시작: {patient_id}")
        logger.info(f"========================================")

        # 중요: 환자 1명당 하나의 StudyInstanceUID 생성 및 공유
        study_uid = pydicom.uid.generate_uid()
        logger.info(f"🔑 생성된 StudyInstanceUID: {study_uid}")

        nii_files = sorted(patient_path.glob('*.nii.gz'))
        if not nii_files:
            logger.warning(f"⚠️  NIfTI 파일이 없습니다: {patient_dir}")
            return

        for i, nii_file in enumerate(nii_files, 1):
            series_number = i
            logger.info(f"\n   📄 시리즈 처리 중 ({i}/{len(nii_files)}): {nii_file.name}")
            
            dicom_files = self.create_dicom_from_nifti(
                nii_file,
                patient_id,  # Patient ID
                study_uid,   # Unified Study UID
                series_number=series_number
            )

            # 업로드
            if dicom_files:
                logger.info(f"   📤 Orthanc 업로드 중 ({len(dicom_files)}장)...")
                for dcm in dicom_files:
                    self.upload_dicom_to_orthanc(dcm)
            
            # 임시 파일 정리 (시리즈 단위)
            temp_dir = Path(f"temp_dicom/{patient_id}/{series_number}")
            if temp_dir.exists():
                shutil.rmtree(temp_dir)
        
        # 환자 단위 정리
        patient_temp_dir = Path(f"temp_dicom/{patient_id}")
        if patient_temp_dir.exists():
            shutil.rmtree(patient_temp_dir)


def main():
    """메인 실행 함수"""

    ORTHANC_URL = 'http://localhost:8042'
    
    # 처리할 환자 디렉토리 목록
    PATIENT_DIRS = [
        r'C:\Users\302-28\Downloads\sub\sub-0004',
        r'C:\Users\302-28\Downloads\sub\sub-0005',
    ]

    logger.info("="* 80)
    logger.info("🏥 NIfTI → DICOM 변환 (Optimized)")
    logger.info("=" * 80)
    logger.info(f"Target Orthanc: {ORTHANC_URL}")

    converter = NIfTIToDICOMConverter(orthanc_url=ORTHANC_URL)

    for patient_dir in PATIENT_DIRS:
        converter.process_patient(patient_dir)

    logger.info("\n" + "=" * 80)
    logger.info(f"🎉 작업 완료!")
    logger.info(f"성공: {converter.success_count}, 실패: {converter.fail_count}")
    logger.info("=" * 80)


if __name__ == '__main__':
    main()

#!/usr/bin/env python
"""
NeuroNova CDSS - Sample DICOM Upload Script

Uploads DICOM files from sample_dicoms directory to Orthanc PACS

Usage:
    python manage.py upload_sample_dicoms
    python manage.py upload_sample_dicoms --patient P20250001  # Specific patient only
    python manage.py upload_sample_dicoms --dry-run  # Test without uploading
"""

import os
import glob
import pydicom
import requests
from django.core.management.base import BaseCommand
from django.conf import settings
from pathlib import Path


class Command(BaseCommand):
    help = 'Upload sample DICOM files to Orthanc PACS'

    def add_arguments(self, parser):
        parser.add_argument(
            '--patient',
            type=str,
            help='Upload only for specific patient ID (e.g., P20250001)',
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Test mode - do not actually upload files',
        )
        parser.add_argument(
            '--path',
            type=str,
            default='sample_dicoms',
            help='Path to sample_dicoms directory (default: sample_dicoms)',
        )

    def handle(self, *args, **options):
        patient_filter = options.get('patient')
        dry_run = options.get('dry_run')
        dicoms_path = options.get('path')

        # 프로젝트 루트 기준 경로
        project_root = Path(settings.BASE_DIR).parent.parent
        dicoms_dir = project_root / dicoms_path

        if not dicoms_dir.exists():
            self.stdout.write(self.style.ERROR(f'[ERROR] DICOM directory not found: {dicoms_dir}'))
            return

        self.stdout.write(self.style.SUCCESS(f'[INFO] Scanning DICOM files in: {dicoms_dir}'))

        # Orthanc 설정
        orthanc_url = getattr(settings, 'ORTHANC_API_URL', 'http://localhost:8042')
        orthanc_user = getattr(settings, 'ORTHANC_USERNAME', None)
        orthanc_pass = getattr(settings, 'ORTHANC_PASSWORD', None)

        self.stdout.write(f'[INFO] Orthanc URL: {orthanc_url}')

        # DICOM 파일 찾기
        dicom_files = self._find_dicom_files(dicoms_dir, patient_filter)

        if not dicom_files:
            self.stdout.write(self.style.WARNING('[WARNING] No DICOM files found'))
            return

        self.stdout.write(f'[INFO] Found {len(dicom_files)} DICOM files')

        if dry_run:
            self.stdout.write(self.style.WARNING('[DRY RUN] Files will not be uploaded'))
            self._show_dry_run_summary(dicom_files)
            return

        # 업로드 실행
        uploaded, failed = self._upload_dicoms(dicom_files, orthanc_url, orthanc_user, orthanc_pass)

        # 결과 출력
        self._print_summary(uploaded, failed, orthanc_url)

    def _find_dicom_files(self, base_dir, patient_filter=None):
        """DICOM 파일 찾기"""
        dicom_files = []

        # sample_dicoms 구조: sub-XXXX/Study/Series/slice_XXX.dcm
        for patient_dir in base_dir.glob('sub-*'):
            # 환자 필터 적용
            if patient_filter and patient_filter not in patient_dir.name:
                continue

            self.stdout.write(f'   Scanning {patient_dir.name}...')

            for dcm_file in patient_dir.rglob('*.dcm'):
                dicom_files.append(dcm_file)

        return dicom_files

    def _upload_dicoms(self, dicom_files, orthanc_url, username, password):
        """DICOM 파일 업로드"""
        uploaded = []
        failed = []

        auth = (username, password) if username and password else None
        upload_url = f'{orthanc_url}/instances'

        for i, dcm_file in enumerate(dicom_files, 1):
            try:
                # DICOM 파일 읽기
                with open(dcm_file, 'rb') as f:
                    dcm_data = f.read()

                # Orthanc에 업로드
                response = requests.post(
                    upload_url,
                    data=dcm_data,
                    headers={'Content-Type': 'application/dicom'},
                    auth=auth,
                    timeout=30
                )

                if response.status_code in [200, 201]:
                    uploaded.append(dcm_file)
                    instance_info = response.json()
                    instance_id = instance_info.get('ID', 'unknown')

                    # 진행 상황 출력
                    if i % 10 == 0 or i == len(dicom_files):
                        self.stdout.write(
                            f'   ✓ Uploaded: {i}/{len(dicom_files)} - {dcm_file.name} (ID: {instance_id[:8]}...)'
                        )
                else:
                    failed.append((dcm_file, f'HTTP {response.status_code}'))
                    self.stdout.write(
                        self.style.WARNING(f'   ✗ Failed: {dcm_file.name} - {response.status_code}')
                    )

            except requests.exceptions.ConnectionError:
                failed.append((dcm_file, 'Connection refused - Is Orthanc running?'))
                self.stdout.write(
                    self.style.ERROR(f'   ✗ Connection error: Is Orthanc running at {orthanc_url}?')
                )
                break  # 연결 실패 시 중단

            except Exception as e:
                failed.append((dcm_file, str(e)))
                self.stdout.write(
                    self.style.WARNING(f'   ✗ Error uploading {dcm_file.name}: {str(e)}')
                )

        return uploaded, failed

    def _show_dry_run_summary(self, dicom_files):
        """Dry run 모드 요약"""
        self.stdout.write('\n' + '='*60)
        self.stdout.write('[DRY RUN] SUMMARY')
        self.stdout.write('='*60)

        # 환자별 그룹화
        patients = {}
        for dcm_file in dicom_files:
            # sub-XXXX 추출
            patient_id = dcm_file.parts[-4] if len(dcm_file.parts) >= 4 else 'unknown'
            study = dcm_file.parts[-3] if len(dcm_file.parts) >= 3 else 'unknown'
            series = dcm_file.parts[-2] if len(dcm_file.parts) >= 2 else 'unknown'

            key = f'{patient_id}/{study}/{series}'
            patients[key] = patients.get(key, 0) + 1

        for patient_path, count in patients.items():
            self.stdout.write(f'   - {patient_path}: {count} files')

        self.stdout.write(f'\n[INFO] Total: {len(dicom_files)} files would be uploaded')
        self.stdout.write('='*60 + '\n')

    def _print_summary(self, uploaded, failed, orthanc_url):
        """업로드 결과 요약"""
        self.stdout.write('\n' + '='*60)
        self.stdout.write(self.style.SUCCESS('[SUMMARY] UPLOAD COMPLETE'))
        self.stdout.write('='*60)

        self.stdout.write(f'\n[SUCCESS] Successfully uploaded: {len(uploaded)} files')

        if failed:
            self.stdout.write(f'[FAILED] Failed: {len(failed)} files')
            self.stdout.write('\nFailed files:')
            for dcm_file, error in failed[:10]:  # Show first 10 failures
                self.stdout.write(f'   • {dcm_file.name}: {error}')
            if len(failed) > 10:
                self.stdout.write(f'   ... and {len(failed) - 10} more')

        # Orthanc 정보 조회
        try:
            response = requests.get(f'{orthanc_url}/statistics')
            if response.status_code == 200:
                stats = response.json()
                self.stdout.write(f'\n[STATS] Orthanc Statistics:')
                self.stdout.write(f'   - Total Studies: {stats.get("CountStudies", "N/A")}')
                self.stdout.write(f'   - Total Series: {stats.get("CountSeries", "N/A")}')
                self.stdout.write(f'   - Total Instances: {stats.get("CountInstances", "N/A")}')
                self.stdout.write(f'   - Disk Size: {stats.get("TotalDiskSizeMB", "N/A")} MB')
        except:
            pass

        self.stdout.write(f'\n[INFO] View in Orthanc: {orthanc_url}/app/explorer.html')
        self.stdout.write('='*60 + '\n')

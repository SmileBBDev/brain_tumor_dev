"""
HTJ2K 압축 효과 비교를 위한 API
"""

from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework import status
from django.http import HttpResponse, StreamingHttpResponse
from django.shortcuts import render
import requests
import time
import random

ORTHANC_URL = 'http://localhost:8042'


def htj2k_comparison_page(request):
    """HTJ2K 비교 테스트 페이지"""
    return render(request, 'ris/htj2k_comparison.html')


@api_view(['GET'])
@permission_classes([AllowAny])
def get_patients_for_comparison(request):
    """
    Orthanc에서 환자 목록 조회
    """
    try:
        response = requests.get(f'{ORTHANC_URL}/patients')
        response.raise_for_status()

        patients = []
        for patient_id in response.json():
            patient_info = requests.get(f'{ORTHANC_URL}/patients/{patient_id}').json()
            main_tags = patient_info.get('MainDicomTags', {})

            patients.append({
                'id': patient_id,
                'patientId': main_tags.get('PatientID', 'Unknown'),
                'patientName': main_tags.get('PatientName', 'Unknown'),
                'studyCount': len(patient_info.get('Studies', []))
            })

        return Response(patients)

    except Exception as e:
        return Response(
            {'error': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([AllowAny])
def get_patient_studies(request, patient_id):
    """
    특정 환자의 Study 목록 조회
    """
    try:
        patient_info = requests.get(f'{ORTHANC_URL}/patients/{patient_id}').json()

        studies = []
        for study_id in patient_info.get('Studies', []):
            study_info = requests.get(f'{ORTHANC_URL}/studies/{study_id}').json()
            main_tags = study_info.get('MainDicomTags', {})

            # Study의 인스턴스 조회
            instances_response = requests.get(f'{ORTHANC_URL}/studies/{study_id}/instances')
            instances_data = instances_response.json() if instances_response.status_code == 200 else []

            # 첫 번째 인스턴스의 Transfer Syntax 확인
            transfer_syntax = "Unknown"
            if instances_data:
                first_instance = instances_data[0]
                inst_tags_response = requests.get(
                    f'{ORTHANC_URL}/instances/{first_instance["ID"]}/tags?simplify'
                )
                if inst_tags_response.status_code == 200:
                    inst_tags = inst_tags_response.json()
                    transfer_syntax = inst_tags.get('TransferSyntaxUID', 'Unknown')

            studies.append({
                'id': study_id,
                'studyDescription': main_tags.get('StudyDescription', 'Unknown'),
                'studyDate': main_tags.get('StudyDate', 'Unknown'),
                'instanceCount': len(instances_data),
                'transferSyntax': transfer_syntax,
                'isHTJ2K': transfer_syntax == '1.2.840.10008.1.2.4.201'
            })

        return Response(studies)

    except Exception as e:
        return Response(
            {'error': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([AllowAny])
def get_study_instances(request, study_id):
    """
    Study의 인스턴스 목록 조회
    """
    try:
        # Orthanc의 /studies/{id}/instances 엔드포인트 사용
        instances_response = requests.get(f'{ORTHANC_URL}/studies/{study_id}/instances')
        instances_response.raise_for_status()
        instances_data = instances_response.json()

        instances = []
        # 처음 10개만 사용
        for instance_info in instances_data[:10]:
            instance_id = instance_info.get('ID')
            main_tags = instance_info.get('MainDicomTags', {})

            instances.append({
                'id': instance_id,
                'instanceNumber': main_tags.get('InstanceNumber', 'Unknown'),
                'seriesDescription': main_tags.get('SeriesDescription', 'Unknown')
            })

        return Response(instances)

    except Exception as e:
        return Response(
            {'error': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([AllowAny])
def download_dicom_standard(request, instance_id):
    """
    일반 DICOM 다운로드 (원본)
    """
    try:
        start_time = time.time()

        response = requests.get(f'{ORTHANC_URL}/instances/{instance_id}/file', stream=True)
        response.raise_for_status()

        download_time = time.time() - start_time

        # 스트리밍 응답
        http_response = HttpResponse(
            response.content,
            content_type='application/dicom'
        )
        http_response['Content-Disposition'] = f'attachment; filename="dicom_{instance_id[:8]}.dcm"'
        http_response['X-Download-Time'] = str(download_time)
        http_response['X-File-Size'] = str(len(response.content))
        http_response['X-Format'] = 'standard'

        return http_response

    except Exception as e:
        return Response(
            {'error': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([AllowAny])
def download_dicom_htj2k_simulated(request, instance_id):
    """
    HTJ2K 시뮬레이션 다운로드

    실제 HTJ2K 변환은 Orthanc 플러그인이 필요하므로,
    시뮬레이션으로 압축률을 적용합니다.

    HTJ2K는 일반적으로 40-60% 압축률을 보입니다.
    """
    try:
        start_time = time.time()

        response = requests.get(f'{ORTHANC_URL}/instances/{instance_id}/file', stream=True)
        response.raise_for_status()

        original_size = len(response.content)

        # HTJ2K 압축률 시뮬레이션 (40-60% 압축)
        compression_ratio = random.uniform(0.4, 0.6)
        simulated_size = int(original_size * compression_ratio)

        # 다운로드 시간도 압축률에 비례하여 시뮬레이션
        simulated_download_time = (time.time() - start_time) * compression_ratio

        # 실제로는 원본 데이터를 전송하지만, 헤더에 시뮬레이션 정보 포함
        http_response = HttpResponse(
            response.content,
            content_type='application/dicom'
        )
        http_response['Content-Disposition'] = f'attachment; filename="dicom_htj2k_{instance_id[:8]}.dcm"'
        http_response['X-Download-Time'] = str(simulated_download_time)
        http_response['X-File-Size'] = str(simulated_size)
        http_response['X-Original-Size'] = str(original_size)
        http_response['X-Compression-Ratio'] = f'{compression_ratio:.2f}'
        http_response['X-Format'] = 'htj2k-simulated'

        return http_response

    except Exception as e:
        return Response(
            {'error': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([AllowAny])
def get_study_statistics(request, study_id):
    """
    Study의 통계 정보 (용량, 인스턴스 수 등)
    """
    try:
        # Study의 인스턴스 조회
        instances_response = requests.get(f'{ORTHANC_URL}/studies/{study_id}/instances')
        instances_response.raise_for_status()
        instances_data = instances_response.json()

        total_size = 0
        # 최대 100개까지 용량 계산
        for instance_info in instances_data[:100]:
            instance_id = instance_info.get('ID')
            file_size = instance_info.get('FileSize', 0)
            total_size += file_size

        # HTJ2K 압축 시뮬레이션
        avg_compression = 0.5  # 50% 압축
        htj2k_size = int(total_size * avg_compression)

        return Response({
            'studyId': study_id,
            'instanceCount': len(instances_data),
            'standardSize': total_size,
            'htj2kSize': htj2k_size,
            'savingsPercent': (1 - avg_compression) * 100,
            'standardSizeMB': round(total_size / (1024 * 1024), 2),
            'htj2kSizeMB': round(htj2k_size / (1024 * 1024), 2)
        })

    except Exception as e:
        return Response(
            {'error': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
